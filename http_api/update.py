from concurrent.futures import ThreadPoolExecutor
import time
import json
import sqlite3
import os

import database
import fetch

update_executor = ThreadPoolExecutor(max_workers=1)  # 由于拉取论文需要的时间太长，这里使用异步应用。
update_task = None  # 拉取论文的任务
database_last_update = 0  # 最后的数据库更新时间，
update_process = ""  # update函数的处理状态
update_process_percent = 0.0  # update函数处理的完成率
last_update = {"message": "Not updated yet!"}


def update_sync():
    global update_task
    global database_last_update
    global last_update
    if update_task is not None and update_task.done():
        e = update_task.exception()
        update_task = None
        if e is None:
            last_update = {"message": "Done!", "last_update": database_last_update}
        else:
            last_update = {"message": "Server Error", "last_update": database_last_update, "error": str(e)}

    if update_task is None:
        if time.time() - database_last_update > 10800:  # 3小时冷却时间
            update_task = update_executor.submit(update)
            database_last_update = time.time()
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
    start_offset = (total_essay - 1) // 1000 * 1000  # 由于是从后往前翻页，故计算开始的offset值
    last_updated = database.latest_update_time(con)  # 得到数据库中最晚更新的论文的时间戳，晚于其更新的论文都是未插入数据库的

    update_process = "GETTING ESSAYS INFO"
    essay_to_insert = []
    pdf_to_fetch = []
    break_flag = False
    for i in range(start_offset, -1, -1000):
        update_process_percent = 1 - (i / total_essay)
        essays = list()  # 论文集
        trail_counter = 0  # 失败计数器，由于此处是频繁拉取所以需要多次尝试机会
        while essays is None or len(essays) == 0:
            if trail_counter >= 5:  # 超出尝试次数，服务器错误
                return {"result": False}, 500
            status, essays = fetch.fetch_data(i, 1000)  # 尝试去拉取
            trail_counter = trail_counter + 1
        for essay in essays:
            # 要插入的论文，更新必须晚于数据库中更新最晚的论文，且不位于数据库中
            if essay["updated"] > last_updated or len(database.query(con, "id", essay["id"])) == 0:
                essay_to_insert.append(essay)
                if 1609430400 > essay["updated"] >= 1601481600:  # 在2020年10月1日后发表,2021年1月1日前停止记录,先记录要下载的pdf
                    pdf_to_fetch.append((essay["pdf"], essay["id"]))
            else:
                break_flag = True  # 由于返回值论文是从晚到早的，若出现了相同的论文，必定是之前已经插入到数据库的论文
                break
        if break_flag:
            break

    update_process = "INSERT INTO DATABASE"
    database.insert(con, essay_to_insert)  # 向数据库里push数据

    if os.path.exists("pdf_list.tmp"):
        temp_file = open("pdf_list.tmp")
        pdf_to_fetch.extend(json.loads(temp_file.read()))
        temp_file.close()
    temp_file = open("pdf_list.tmp", "w")
    temp_file.write(json.dumps(pdf_to_fetch))
    temp_file.close()
    update_process = "DOWNLOADING PDF"
    count = 1
    for essay in pdf_to_fetch:  # 此处开始下载pdf
        update_process_percent = count / len(pdf_to_fetch)
        fetch.download_pdf(essay[0], essay[1])
        count = count + 1
    if os.path.exists("pdf_list.tmp"):
        os.remove("pdf_list.tmp")
    con.close()


def return_update_process():
    global update_task
    if update_task is None:
        return json.dumps({"status": 0, "message": "Not Updating"})
    else:
        if update_task.done():
            return json.dumps({"status": 2, "message": "Done"})
        else:
            return json.dumps({"status": 1, "message": update_process, "percent": update_process_percent})


if __name__ == 'main':
    pass
