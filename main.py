import fetch
import database
import sqlite3
import flask
import os
from flask import g

server = flask.Flask(__name__)


def get_db():
    con = getattr(g, '_database', None)
    if con in None:
        con = sqlite3.connect("essay.db")
    return con


@server.route('/update', methods=['get'])
def update():
    con = get_db()
    database.init(con)  # 初始化数据库
    fetch_status, total_essay = fetch.total_essay_number()  # 得到当前cs.AI分类下的所有论文数
    print("GET ESSAY")
    if not fetch_status:  # 如果拉取失败，返回服务器错误
        return {"result": False}, 500
    start_offset = (total_essay - 1) // 1000 * 1000  # 由于是从后往前翻页，故计算开始的offset值
    last_updated = database.latest_update_time(con)  # 得到数据库中最晚更新的论文的时间戳，晚于其更新的论文都是未插入数据库的
    for i in range(start_offset, -1, -1000):
        essays = list()  # 论文集
        trail_counter = 0  # 失败计数器，由于此处是频繁拉取所以需要多次尝试机会
        while essays is None or len(essays) == 0:
            if trail_counter >= 5:  # 超出尝试次数，服务器错误
                return {"result": False}, 500
            status, essays = fetch.fetch_data(i, 1000)  # 尝试去拉取
            trail_counter = trail_counter + 1
            print("GET ESSAYS")
        insert_status = database.insert(con, essays, last_updated)  # 向数据库里push数据
        if not insert_status:  # 如果遇到了相同的数据，则停止push，由于数据无法更改之后的数据一定相等
            print("BREAKED!")
            break
        print("PERCENT {}/{}".format(i, total_essay))
    return {"result": True}, 201


@server.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@server.route('/query', methods=['post'])
def query():
    query_request = flask.request.get_json()
    key = query_request['key']
    query_string = query_request['query']
    strict = query_request['strict']
    con = get_db()
    database.init(con)
    if strict is not None:
        strict = True
    else:
        strict = False
    essays = database.query(con, key, query_string, strict)
    return {"result": True, "essays": essays}, 200


@server.route('/pdf', methods=['post'])
def get_pdf(arxiv_id):
    query_request = flask.request.get_json()
    arxiv_id = query_request['arxiv_id']
    filename = str(arxiv_id) + ".pdf"
    filepath = os.path.join('./pdf', filename)
    if os.path.exists(filepath):
        return flask.send_from_directory(filepath, filename), 200
    else:
        return "", 404


if __name__ == '__main__':
    server.run(port=10501, host='0.0.0.0')
