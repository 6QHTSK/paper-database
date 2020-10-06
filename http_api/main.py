from . import fetch
from . import database
import sqlite3
import flask
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from flask import g

server = flask.Flask(__name__)
update_executor = ThreadPoolExecutor(max_workers=1) # 由于拉取论文需要的时间太长，这里使用异步应用。
update_task = None # 拉取论文的编号
database_last_update = 0 # 最后的数据库更新时间，
update_process = "" # update函数的处理状态
update_process_percent = 0.0 # update函数处理的完成率


def get_db():
    """
    在flask框架下调用sqlite数据库
    :return: 拿到的数据库的连接
    """
    con = getattr(g, '_database', None)
    if con is None:
        con = sqlite3.connect("essay.db")
    return con


@server.route('/update', methods=['get'])
def update_request():
    """
    处理前端发来的请求更新请求（异步处理）
    :return: 更新信息（开始更新，更新状态，更新冷却，错误情况）等
    """
    global update_task
    global database_last_update
    if update_task is None:
        if time.time() - database_last_update > 10800: # 3小时冷却时间
            update_task = update_executor.submit(update)
            database_last_update = time.time()
            return json.dumps({"result": True, "message": "Started!"}), 202
        else:
            return json.dumps({"result": False, "message": "Update is Cooling Down!"}), 400
    else:
        if update_task.done():
            e = update_task.exception()
            update_task = None
            if e is None:
                return json.dumps({"result": True, "message": "Done!"}), 200
            else:
                return json.dumps({"result": False, "message": "Server Error", "error": str(e)}), 500
        else:
            return json.dumps({"result": True, "message": update_process, "percent": update_process_percent}), 202


def update():
    """
    更新数据库，异步函数
    :param con: 需要操作的数据库
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
            if essay["updated"] >= last_updated or database.query(con, "id", essay["id"]) == 0:
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

    update_process = "DOWNLOADING PDF"
    count = 1
    for essay in pdf_to_fetch:  # 此处开始下载pdf
        update_process_percent = count / len(pdf_to_fetch)
        fetch.download_pdf(essay[0], essay[1])
        count = count + 1
    con.close()


@server.teardown_appcontext
def close_db(exception):
    """
    database的取消连接
    :param exception:
    :return: 无返回
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@server.route('/query', methods=['get'])
def query():
    """
    查询函数，支持模糊查询
    json传入，key：查询的列(输错返回空列表），query：查询字符串，strict：False为模糊查询
    :return: 查询到的论文
    """
    query_request = flask.request.get_json()
    key = query_request['key']
    query_string = query_request['query']
    strict = query_request['strict']
    con = get_db()
    database.init(con)
    if strict is None:
        strict = True
    essays = database.query(con, key, query_string, strict)
    return json.dumps(essays), 200


@server.route('/pdf/<arxiv_id>', methods=['get'])
def get_pdf(arxiv_id):
    """
    返回服务器上储存的pdf文件
    :param arxiv_id: 需要下载的论文的arxiv_id
    :return: 下载的论文
    """
    filename = str(arxiv_id).replace(':', '_') + ".pdf"
    filepath = os.path.join('.\\Artificial Intelligence\\', filename)
    if os.path.exists(filepath):
        # return flask.send_from_directory(filepath, filename), 200
        return flask.send_file(filepath)
    else:
        return "", 404


if __name__ == '__main__':
    server.run(port=10501, host='0.0.0.0')
