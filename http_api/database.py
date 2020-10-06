"""
包装数据库接口的程序
含有函数：
init
query
insert
"""
import json


def init(con):
    """
    初始化数据库，在装载api时需要调用
    :param con: 由调用者传来的数据库对象
    :return: 无返回值
    """
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS essays(id TEXT, title TEXT, authors TEXT, summary TEXT, category TEXT, "
                "pdf TEXT, essay_details TEXT, updated INTEGER, published INTEGER, primary_category TEXT, "
                "comment TEXT, journal_ref TEXT, doi TEXT)")
    con.commit()


def query(con, key, query_str, strict=True):
    """
    查找数据库元素
    :param con: 数据库对象
    :param key: 查询的条目-字符串
    :param query_str: 查询字符串，不支持正则
    :param strict: 是否使用模糊查询，模糊查询将此项置为False，默认不使用模糊查询
    :return: 由含有论文信息的字典构成的列表
    """
    cur = con.cursor()
    results = []
    available_keys = ["id", "title", "authors", "summary", "category", "pdf", "essay_details", "updated", "published",
                      "primary_category", "comment", "journal_ref", "doi"]
    if key in available_keys:
        if strict:  # 是否使用模糊查询
            cur.execute("SELECT * from essays where {} like ?".format(key), (query_str,))
        else:
            cur.execute("SELECT * from essays where {} like ?".format(key), ("%" + query_str + "%",))
        raw_results = cur.fetchall()  # 拉取所有数据库查询到的信息
        for raw_result in raw_results:
            # 将数据库存储的信息转化成更易读取的字典形式
            result = {"id": raw_result[0], "title": raw_result[1], "authors": json.loads(raw_result[2]),
                      "summary": raw_result[3], "category": json.loads(raw_result[4]), "pdf": raw_result[5],
                      "essay_details": raw_result[6], "updated": raw_result[7], "published": raw_result[8],
                      "primary_category": raw_result[9], "comment": raw_result[10], "journal_ref": raw_result[11],
                      "doi": raw_result[12]}
            results.append(result)
    return results


def insert(con, essays):
    """
    不经处理的向数据库插入一组论文信息
    :param con: 调用的数据库
    :param essays: 论文信息字典列表
    :param last_updated: 插入截至的时间
    :return: None
    """
    cur = con.cursor()
    for essay in essays:
        cur.execute("INSERT INTO essays VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            essay["id"], essay["title"], json.dumps(essay["authors"]), essay["summary"],
            json.dumps(essay["category"]),
            essay["pdf"], essay["essay_details"], essay["updated"], essay["published"], essay["primary_category"],
            essay["comment"], essay["journal_ref"], essay["doi"]
        ))  # 将论文放入数据库
    con.commit()


def latest_update_time(con):
    """
    返回数据库中updated时间最晚的时间戳
    :return: 时间戳
    """
    cur = con.cursor()
    cur.execute("SELECT max(updated) from essays")
    last_update = cur.fetchone()[0]
    if last_update is None:
        last_update = 0
    return last_update