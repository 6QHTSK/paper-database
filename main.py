import fetch
import database
import sqlite3
import flask


def update():
    con = sqlite3.connect("essay.db")
    database.init(con)
    fetch_status, total_essay = fetch.total_essay_number()
    print("GET ESSAY")
    if not fetch_status:
        return {"result": False}, 500
    for i in range(0, total_essay, 1000):
        status, essays = fetch.fetch_data(i)
        if not status:
            return {"result": False}, 500
        flag = False
        for essay in essays:
            insert_status = database.insert(con, essay)
            if not insert_status:
                flag = True
                break
        if flag:
            break
        print("PERCENT {}/{}".format(i, total_essay))
    return {"result": True}, 201


def query(key, query_string):
    con = sqlite3.connect("essay.db")
    database.init(con)
    essays = database.query(con, key, query_string)
    return {"result": True, "essays": essays}, 200

update()