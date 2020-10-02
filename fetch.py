from bs4 import BeautifulSoup
import requests as rq
import time


def fetch_data(start_year, end_year, offset):
    essays = []
    for year in range(start_year, end_year):
        search_result = rq.get(
            "https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=cs.AI&terms-0-field=all"
            "&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list"
            "=include&date-filter_by=specific_year&date-year={}"
            "&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order"
            "=-announced_date_first&start={}".format(year, offset))  # 拉取搜索页面的超长网址

        if search_result.status_code != 200:  # 非正常返回，返回报错
            return False, None

        search_soup = BeautifulSoup(search_result.text, features="html.parser") # 使用BeautifulSoup识别网页

        if search_soup.find("h1", class_="title").text.strip().find("no results") != -1:  # 找不到，返回报错
            return False, None

        lines = search_soup.find_all("li", class_="arxiv-result") # 解析所有该页的的条目

        for line in lines:
            essay = {"id": line.find("p", class_="list-title").find("a").text.strip(),  # id:arxiv id
                     "title": line.find("p", class_="title").text.strip(), "authors": [], # title: 文章标题，author: 作者的列表
                     "abstract": line.find("p", class_="abstract").find("span", class_="abstract-full").text.strip(), # abstract 摘要
                     "tags": []}  # tags 标签的列表
            tags = line.find("div", class_="tags").find_all("span", class_="tag") # 读取 tag 信息
            for tag in tags:
                essay["tags"].append(tag.text.strip()) # tag存放于span标签中，此处剥去span外壳

            authors = line.find("p", class_="authors").find_all("a") # 读取author 信息
            for author in authors:
                essay["authors"].append(author.text.strip()) # author 存放与a标签中，此处剥去a标签
            times = line.find("p", class_="is-size-7").contents # 提交时间和宣布时间所在的p是最早出现 is-size-7 class 的地方
            essay["submitted_time"] = times[1].strip() # 提交时间，这里写死了
            essay["originally_announced"] = times[3].strip() # 宣布时间，这里写死了
            comments = line.find_all("p", class_="comments") # comments部分，可能有多个部分
            if comments is not None:
                for comment in comments:
                    if comment.contents[1].text.strip() == "Comments:": # 一般的comments
                        essay["comments"] = comment.text.replace("Comments:", "").strip()
                    elif comment.contents[1].text.strip() == "Journal ref:": # 引用
                        essay["journal_ref"] = comment.text.replace("Journal ref:", "").strip()
                    else: # 好像到这里的基本上都是那几个编号，明天给它加一下识别
                        if essay["other_comments"] is None:
                            essay["other_comments"] = [comment.text.strip()]
                        else:
                            essay["other_comments"].append(comment.text.strip())
            essays.append(essay) # 将本片文章加入文章的集合中

        time.sleep(2) # 休息两秒，防止api爬虫被封
    return True, essays # 返回文章集合中


if "__name__" == "__main__":
    fetch_data(1993, time.localtime(time.time()).tm_year + 1, 0)
