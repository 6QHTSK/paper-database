import asyncio
import requests
import json
import time
import math


from graia.application import GraiaMiraiApplication, Session
from graia.application.event.messages import FriendMessage
from graia.application.friend import Friend
from graia.application.message.chain import MessageChain
from graia.application.group import Group
from graia.application.message.elements.internal import Plain
from graia.broadcast import Broadcast

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080",  # 填入 httpapi 服务运行的地址
        authKey="INITKEYgxbz60uS",  # 填入 authKey
        account=3526677106,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)


@bcc.receiver("FriendMessage")
async def group_message_handler(message: MessageChain, friend: Friend, graia_app: GraiaMiraiApplication):
    request_text = message[Plain][0].text
    request_parm = request_text.split()
    if len(request_parm) > 1:
        if request_parm[0].lower() == "search":
            search_flag = "query"
            search = {"key": "all", "strict": False, "page": '0'}
            temp_str = ""
            start = 0
            for i in range(1, len(request_parm)):
                parm = request_parm[i]
                if parm == "-key":
                    search[search_flag] = temp_str.strip()
                    search_flag = "key"
                    temp_str = ""
                elif parm == "-page":
                    search[search_flag] = temp_str.strip()
                    search_flag = "page"
                    temp_str = ""
                elif parm == "-strict":
                    search[search_flag] = temp_str.strip()
                    search["strict"] = True
                    temp_str = ""
                else:
                    temp_str = temp_str + parm + ' '
            if temp_str != "":
                search[search_flag] = temp_str.strip()
            if search["page"].isdigit():
                start = int(search["page"])
            headers = {'Content-Type': 'application/json'}
            response = requests.get(url="http://localhost:10501/query", headers=headers, data=json.dumps(search))
            try:
                response_json = response.json()
            except:
                await app.sendFriendMessage(friend, MessageChain.create([Plain("连接查询服务器失败")]))
                return
            return_str = "共为你找到{}篇论文，页码{}/{}：\r".format(len(response_json), start, math.ceil(len(response_json)/5))
            for i in range(start*10, len(response_json)):
                if i >= start * 10 + 5:
                    break
                print("GENERATE")
                return_str = return_str + "({}):[{}]\r{}\r".format(i + 1, response_json[i]["id"], response_json[i]["title"])
            await app.sendFriendMessage(friend, MessageChain.create([Plain(return_str)]))
            return
        elif request_parm[0].lower() == "detail":
            arxiv_id = ""
            for i in range(1, len(request_parm)):
                parm = request_parm[i]
                arxiv_id = arxiv_id + parm + " "
            arxiv_id = arxiv_id.strip()

            data = {"key": "id", "query": arxiv_id, "strict": False}
            headers = {'Content-Type': 'application/json'}
            response = requests.get(url="http://localhost:10501/query", headers=headers, data=json.dumps(data))
            try:
                response_json = response.json()
            except:
                await app.sendFriendMessage(friend, MessageChain.create([Plain("连接查询服务器失败")]))
                return
            if len(response_json) == 1:
                return_str = "你要找的论文是不是\r [{}]\r".format(response_json[0]["id"])
                return_str = return_str + "标题： {}\r".format(response_json[0]["title"])
                return_str = return_str + "作者： "
                for author in response_json[0]["authors"]:
                    return_str = return_str + author + ", "
                return_str = return_str + "\r标签："
                for tag in response_json[0]["category"]:
                    return_str = return_str + tag + ", "
                return_str = return_str + "\r主要方向： {}\r".format(response_json[0]["primary_category"])
                return_str = return_str + "详细信息： {}\r".format(response_json[0]["essay_details"])
                return_str = return_str + "论文下载： {}\r".format(response_json[0]["pdf"])
                await app.sendFriendMessage(friend, MessageChain.create([Plain(return_str)]))
                return
            elif len(response_json) == 0:
                await app.sendFriendMessage(friend, MessageChain.create([Plain("找不到论文")]))
                return
            elif len(response_json) > 1:
                await app.sendFriendMessage(friend, MessageChain.create([Plain("论文太多了，请先用search论文确定论文的arxiv_id\r当前搜索到的论文数：{}".format(len(response_json)))]))
                return
            return
    elif len(request_parm) == 1:
        if request_parm[0].lower() == "update":
            rq = requests.get("http://localhost:10501/update")
            try:
                update_info = rq.json()
            except:
                await app.sendFriendMessage(friend, MessageChain.create([Plain(str("连接更新服务器失败"))]))
                return
            if update_info["status"] == 0:
                return_info = "已经开始更新"
            elif update_info["status"] == 1:
                return_info = "正在更新中"
            elif update_info["status"] == 2:
                return_info = "更新冷却中，请等待三小时"
            else:
                await app.sendFriendMessage(friend, MessageChain.create([Plain(str("更新服务器错误"))]))
                return
            if "last_update" in update_info:
                last_update = update_info["last_update"]["message"]
                last_update_time = update_info["last_update"]["last_update"]
                last_update_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_update_time))
                return_string = return_info + "\r上次更新：" + last_update + "\r上次更新时间：" + last_update_time_str
            elif "percent" in update_info:
                update_message = update_info["message"]
                update_percent = update_info["percent"]
                return_string = return_info + "\r正在处理： {}\r完成：{}%".format(update_message, round(update_percent*100,1))
            else:
                return_string = return_info
            await app.sendFriendMessage(friend, MessageChain.create([Plain(return_string)]))

app.launch_blocking()
