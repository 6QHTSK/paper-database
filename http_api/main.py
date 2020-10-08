import sqlite3
import flask
import os
import json
from flask_apscheduler import APScheduler
from flask import g

import fetch
import database
import update


class SchedulerConfig(object):
    JOBS = [
        {
            'id': 'update',  # 任务id
            'func': '__main__:update_request',  # 任务执行程序
            'args': None,  # 执行程序参数
            'trigger': 'interval',  # 任务执行类型，定时器
            'seconds': 86400,  # 任务执行时间，单位秒
        }
    ]


server = flask.Flask(__name__)
server.config.from_object(SchedulerConfig())


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
    return update.update_sync()


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


@server.route('/process')
def return_update_process():
    return update.return_update_process


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
        return flask.send_file(filepath)
    else:
        query_result = database.query(get_db(), 'id', arxiv_id)
        if len(query_result) == 1:
            fetch.download_pdf(query_result[0]['pdf'], arxiv_id)
            return flask.send_file(filepath)
        else:
            return "", 404


if __name__ == '__main__':
    update_request()
    scheduler = APScheduler()  # 实例化APScheduler
    scheduler.init_app(server)  # 把任务列表载入实例flask
    scheduler.start()  # 启动任务计划
    server.run(port=10501, host='0.0.0.0')
