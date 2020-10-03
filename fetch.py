"""
用于拉取arxiv上的数据的程序部分
内含函数：
fetch_data
"""
from bs4 import BeautifulSoup
import requests as rq
import time


def _get_time_stamp(time_str):
    """
    将arxiv的时间字符串转换为时间戳
    :param time_str arxiv的时间字符串
    :return: 时间戳
    """
    time_array = time.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    time_stamp = int(time.mktime(time_array))
    return time_stamp


def total_essay_number():
    """
    返回arxiv上的cs.AI相关的所有论文数量
    :return: 是否成功获得（True、False），若成功第二项为论文数量
    """
    search_result = rq.get(
        "http://export.arxiv.org/api/query?search_query=cat:cs.AI")  # 拉取搜索页面的超长网址

    if search_result.status_code != 200:  # 非正常返回，返回报错
        return False, None

    search_soup = BeautifulSoup(search_result.text, features="html.parser")  # 使用BeautifulSoup识别网页

    return True, int(search_soup.find("opensearch:totalresults").text)


def fetch_data(offset, max_results=1000):
    """
    拉取arxiv的论文信息, 默认按时间由晚到早排序
    :param offset: 起始条数的位移，用于翻页
    :param max_results: 单次返回数据的最多条数,默认1000
    :return: True/False，若True则第二项为一个字典组成的列表，包含这部分论文的所有信息
    """
    essays = []
    search_result = rq.get(
        "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=lastUpdatedDate&sortOrder=descending"
        "&start={}&max_results={}".format(offset, max_results))  # 拉取搜索页面的超长网址

    if search_result.status_code != 200:  # 非正常返回，返回报错
        return False, None

    search_soup = BeautifulSoup(search_result.text, features="html.parser")  # 使用BeautifulSoup识别网页
    entries = search_soup.find_all("entry")  # 解析所有该页的的条目

    for entry in entries:
        # 首先对可以直接解析的部分进行解析
        essay = {"id": entry.id.text.replace("http://arxiv.org/abs/", "arxiv:"),
                 "title": entry.title.text.replace('\n', "").strip(),
                 "authors": [], "summary": entry.summary.text.replace('\n', "").strip(), "category": [],
                 "pdf": entry.find("link", title="pdf").attrs["href"], "essay_details": entry.id.text,
                 "updated": _get_time_stamp(entry.updated.text), "published": _get_time_stamp(entry.published.text)}

        category = entry.find_all("category")  # 读取 category 信息，也就是tag
        for tag in category:
            essay["category"].append(tag.attrs["term"])  # 每一个tag存放于term 的 attrs 中

        authors = entry.find_all("author")  # 读取 author 信息
        for author in authors:
            essay["authors"].append(author.find("name").text)  # author 存放于name标签中，此处剥去name标签

        primary_category = entry.find("arxiv:primary_category")  # 主要分类 primary_category 部分, 可能为none
        if primary_category is not None:
            essay["primary_category"] = primary_category.attrs["term"]
        else:
            essay["primary_category"] = None

        comment = entry.find("arxiv:comment")  # comments 部分， 可能为none
        if comment is not None:
            essay["comment"] = comment.text.strip().replace('\n', "")
        else:
            essay["comment"] = None

        journal_ref = entry.find("arxiv:journal_ref")  # journal_ref 部分， 可能为none
        if journal_ref is not None:
            essay["journal_ref"] = journal_ref.text.strip().replace('\n', "")
        else:
            essay["journal_ref"] = None

        doi = entry.find("arxiv:doi")  # doi 部分， 可能为none
        if doi is not None:
            essay["doi"] = doi.text.strip().replace('\n', "")
        else:
            essay["doi"] = None

        essays.append(essay)  # 将本片文章加入文章的集合中

    time.sleep(2)  # 休息两秒，防止api爬虫被封
    return True, essays  # 返回文章集合


if __name__ == "__main__":
    fetch_data(0)
