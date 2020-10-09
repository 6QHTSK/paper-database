import main
import update
import configparser
import os


def generate_config():
    conf = configparser.ConfigParser()
    try:
        conf_file = open("setting.ini", "w")  # 尝试打开setting文件
    except OSError:
        print("Cannot make file")
        raise Exception("Cannot make file")
    # 下面都是设置参数
    conf.add_section("API")
    conf.set("API", "host", '0.0.0.0')
    conf.set("API", "port", '10501')
    conf.add_section("UPDATE")
    conf.set("UPDATE", "update_interval", '86400')
    conf.set("UPDATE", "cool_down", '10800')
    conf.set("UPDATE", "request_max_result", '1000')
    conf.set("UPDATE", "pdf_fetch_start_time", '1601481600')
    conf.set("UPDATE", "pdf_fetch_end_time", '1609430400')
    conf.write(conf_file)


def config():
    conf = configparser.ConfigParser()
    if os.path.exists("setting.ini"):  # 如果存在config文件，则调用设置
        conf.read("setting.ini")
        host = conf.get("API", "host", fallback='0.0.0.0')
        port = conf.getint("API", "port", fallback=10501)
        update_interval = conf.getint("UPDATE", "update_interval", fallback=86400)
        main.init(host, port, update_interval)

        cool_down = conf.getint("UPDATE", "cool_down", fallback=10800)
        request_max_result = conf.getint("UPDATE", "request_max_result", fallback=1000)
        pdf_fetch_start_time = conf.getint("UPDATE", "pdf_fetch_start_time", fallback=1601481600)
        pdf_fetch_end_time = conf.getint("UPDATE", "pdf_fetch_end_time", fallback=1609430400)
        update.init(cool_down, request_max_result, pdf_fetch_start_time, pdf_fetch_end_time)
    else:  # 否则生成设置
        generate_config()
        main.init()
        update.init()


if __name__ == '__main__':
    config()
    main.start()
