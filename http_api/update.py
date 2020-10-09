from concurrent.futures import ThreadPoolExecutor
import time
import json
import sqlite3
import os

import database
import fetch

cool_down = 10800 #拉取冷却时间
request_max_results = 1000 #单次拉取最多结果
pdf_start_time = 1601481600 #pdf拉取最早时间
pdf_end_time = 1609430400 #pdf拉取最晚时间


def init(init_cool_down=10800, init_max_result=1000, init_start_time=1601481600, init_end_time=1609430400):
    '''
    update文件初始化
    :param init_cool_down: 拉取冷却时间初始化
    :param init_max_result: 单次拉取最多结果
    :param init_start_time: pdf拉取最早时间
    :param init_end_time: pdf拉取最晚时间
    :return: 无返回
    '''
    global cool_down, request_max_results, pdf_start_time, pdf_end_time
    cool_down = init_cool_down
    request_max_results = init_max_result
    pdf_start_time = init_start_time
    pdf_end_time = init_end_time


update_executor = ThreadPoolExecutor(max_workers=1)  # 由于拉取论文需要的时间太长，这里使用异步应用。
update_task = None  # 拉取论文的任务
database_last_update = 0  # 最后的数据库更新时间，
update_process = ""  # update函数的处理状态
update_process_percent = 0.0  # update函数处理的完成率
last_update = {"message": "Not updated yet!"} # 先写一个last_update


def update_sync():
    '''
    update函数同步部分
    :return: 回传给api的状态json
    '''
    global update_task
    global database_last_update
    global last_update
    if update_task is not None and update_task.done(): # 如果 上一个update_task已经完成
        e = update_task.exception() # 先看看有没有报错
        update_task = None # 完成后将其置None
        # last_update 情况
        if e is None:
            last_update = {"message": "Done!", "last_update": database_last_update}
        else:
            last_update = {"message": "Server Error", "last_update": database_last_update, "error": str(e)}

    if update_task is None: # 如果当前没有update_task
        if time.time() - database_last_update > cool_down:  # 冷却时间
            update_task = update_executor.submit(update) # 将update任务加入异步任务
            database_last_update = time.time() # 并获得开始更新的时间
            return json.dumps({"result": True, "status": 0, "message": "Started!", "last_update": last_update}), 202
        else:
            return json.dumps(
                {"result": False, "status": 2, "message": "Cooling Down...", "last_update": last_update}), 400
    else:
        return json.dumps(
            {"result": True, "status": 1, "message": update_process, "percent": update_process_percent}), 202


def update():
    """
    更新数据库，异步函数
    :return: 无返回
    """
    global update_process
    global update_process_percent

    update_process = "INITIATING"
    update_process_percent = 0.0
    con = sqlite3.connect('essay.db')
    database.init(con)  # 初始化数据库

    fetch_status, total_essay = fetch.total_essay_number()  # 得到当前cs.AI分类下的所有论文数
    if not fetch_status:  # 如果拉取失败，返回服务器错误
        raise Exception("Cannot get the count of total essay number")
    start_offset = (total_essay - 1) // request_max_results * request_max_results  # 由于是从后往前翻页，故计算开始的offset值
    last_updated = database.latest_update_time(con)  # 得到数据库中最晚更新的论文的时间戳，晚于其更新的论文都是未插入数据库的

    update_process = "GETTING ESSAYS INFO"
    essay_to_insert = []
    pdf_to_fetch = []
    break_flag = False
    for i in range(start_offset, -1, -request_max_results):
        update_process_percent = 1 - (i / total_essay)
        essays = list()  # 论文集
        trail_counter = 0  # 失败计数器，由于此处是频繁拉取所以需要多次尝试机会
        while essays is None or len(essays) == 0:
            if trail_counter >= 5:  # 超出尝试次数，服务器错误
                return
            status, essays = fetch.fetch_data(i, request_max_results)  # 尝试去拉取
            trail_counter = trail_counter + 1
        for essay in essays:
            # 要插入的论文，更新必须晚于数据库中更新最晚的论文，且不位于数据库中
            if essay["updated"] > last_updated or len(database.query(con, "id", essay["id"])) == 0:
                essay_to_insert.append(essay)
                if pdf_end_time > essay["updated"] >= pdf_start_time:  # 在2020年10月1日后发表,2021年1月1日前停止记录,先记录要下载的pdf
                    pdf_to_fetch.append((essay["pdf"], essay["id"]))
            else:
                break_flag = True  # 由于返回值论文是从晚到早的，若出现了相同的论文，必定是之前已经插入到数据库的论文
                break
        if break_flag:
            break

    update_process = "INSERT INTO DATABASE"
    database.insert(con, essay_to_insert)  # 向数据库里push数据

    if os.path.exists("pdf_list.tmp"): # 获取之前缓存的要拉取的pdf的文件
        temp_file = open("pdf_list.tmp")
        pdf_to_fetch.extend(json.loads(temp_file.read()))
        temp_file.close()
    temp_file = open("pdf_list.tmp", "w") # 往pdf_list.tmp文件中放置当前要拉取的pdf，作为缓存
    temp_file.write(json.dumps(pdf_to_fetch))
    temp_file.close()

    update_process = "DOWNLOADING PDF"
    count = 1
    for essay in pdf_to_fetch:  # 此处开始下载pdf
        update_process_percent = count / len(pdf_to_fetch)
        fetch.download_pdf(essay[0], essay[1])
        count = count + 1

    if os.path.exists("pdf_list.tmp"): # 下载完毕，删除pdf_list.tmp
        os.remove("pdf_list.tmp")
    con.close()


def return_update_process():
    '''
    获取当前更新的情况，不进行update
    :return: 当前更新的情况
    '''
    global update_task
    if update_task is None: # 当前没有任务
        return json.dumps({"status": 0, "message": "Not Updating"})
    else:
        if update_task.done(): # 当前任务已完成
            return json.dumps({"status": 2, "message": "Done"})
        else: # 当前任务进行中
            return json.dumps({"status": 1, "message": update_process, "percent": update_process_percent})


if __name__ == 'main':
    pass
