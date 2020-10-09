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
api_url = "http://localhost:10501"

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
    if message.has(Plain):
        request_text = message[Plain][0].text  # 获取传来的数据的要求
        request_parm = request_text.split()  # 将传来的数据split开
        if len(request_parm) > 1:  # 当传来的request可以分为多于一个值的时候
            if request_parm[0].lower() == "search":  # 如果第一个单词是search，则执行查询论文指令
                # 解析传入的查询信息
                search_flag = "query"
                search = {"key": "all", "strict": False, "page": '1'}
                temp_str = ""
                start = 1
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
                del search["page"]  # page 变量暂存与search字典中，search字典将会转化为json发送给服务器

                headers = {'Content-Type': 'application/json'}
                response = requests.get(url=api_url + "/query", headers=headers, data=json.dumps(search))  # 去拉取query结果
                try:
                    response_json = response.json()
                except:
                    await app.sendFriendMessage(friend, MessageChain.create([Plain("连接查询服务器失败")]))
                    return

                # 生成返回结果，一页5个最合适，此处用到了page来翻页
                if len(response_json) == 0:
                    await app.sendFriendMessage(friend, MessageChain.create([Plain("无返回结果")]))
                    return
                if start > math.ceil(len(response_json) / 5) or start <= 0:
                    await app.sendFriendMessage(friend, MessageChain.create([Plain("没有指定的页码")]))
                    return
                return_str = "共为你找到{}篇论文，页码{}/{}：\r".format(len(response_json), start, math.ceil(len(response_json) / 5))
                for i in range((start - 1) * 5, len(response_json)):
                    if i >= (start - 1) * 5 + 5:
                        break
                    return_str = return_str + "({}):[{}]\r{}\r".format(i + 1, response_json[i]["id"],
                                                                       response_json[i]["title"])

                # 生成的数据返回
                await app.sendFriendMessage(friend, MessageChain.create([Plain(return_str)]))
                return

            elif request_parm[0].lower() == "detail":  # 如果是想要得到某个论文的details

                # 从信息中得到请求的arxiv_id
                arxiv_id = ""
                for i in range(1, len(request_parm)):
                    parm = request_parm[i]
                    arxiv_id = arxiv_id + parm + " "
                arxiv_id = arxiv_id.strip()

                # 构造查询用的json
                data = {"key": "id", "query": arxiv_id, "strict": False}
                headers = {'Content-Type': 'application/json'}
                response = requests.get(url=api_url+"/query", headers=headers, data=json.dumps(data))

                # 获取查询结果
                try:
                    response_json = response.json()
                except:
                    await app.sendFriendMessage(friend, MessageChain.create([Plain("连接查询服务器失败")]))
                    return

                # 只有结果为1时才返回具体数据
                if len(response_json) == 1:
                    # 构造返回的字符串
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

                # 无查询结果
                elif len(response_json) == 0:
                    await app.sendFriendMessage(friend, MessageChain.create([Plain("找不到论文")]))
                    return

                # 多个查询结果
                elif len(response_json) > 1:
                    await app.sendFriendMessage(friend, MessageChain.create(
                        [Plain("论文太多了，请先用search, 确定论文的arxiv_id再使用\r当前搜索到的论文数：{}".format(len(response_json)))]))
                    return
                return

        elif len(request_parm) == 1:
            if request_parm[0].lower() == "update": # 传入值为update时，更新

                # 发送更新指令
                rq = requests.get(api_url + "/update")
                try:
                    update_info = rq.json()
                except:
                    await app.sendFriendMessage(friend, MessageChain.create([Plain(str("连接更新服务器失败"))]))
                    return

                # 更新情况转码
                if update_info["status"] == 0:
                    return_info = "已经开始更新"
                elif update_info["status"] == 1:
                    return_info = "正在更新中"
                elif update_info["status"] == 2:
                    return_info = "更新冷却中，请等待三小时"
                else: # 备用分支，一般不触发
                    await app.sendFriendMessage(friend, MessageChain.create([Plain(str("更新服务器错误"))]))
                    return

                # 格式化last_update
                if "last_update" in update_info:
                    last_update = update_info["last_update"]["message"]
                    last_update_time = update_info["last_update"]["last_update"]
                    last_update_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_update_time)) # 格式化时间
                    return_string = return_info + "\r上次更新：" + last_update + "\r上次更新时间：" + last_update_time_str
                elif "percent" in update_info:
                    # 格式化其中的百分比
                    update_message = update_info["message"]
                    update_percent = update_info["percent"]
                    return_string = return_info + "\r正在处理： {}\r完成：{}%".format(update_message,
                                                                              round(update_percent * 100, 1))
                else:
                    return_string = return_info
                await app.sendFriendMessage(friend, MessageChain.create([Plain(return_string)]))
            if request_parm[0].lower() == "help":
                help_str = "search [查询字符串] [-key 查询键] [-page 页码][-strict]\r查询论文(添加 -strict 不使用模糊查询)\r" \
                           "detail [arxiv_id] 查询论文具体信息\r" \
                           "update 更新论文\r" \
                           "help 帮助"
                await app.sendFriendMessage(friend, MessageChain.create([Plain(help_str)]))


app.launch_blocking()
