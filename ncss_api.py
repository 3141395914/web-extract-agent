"""国家大学生就业服务平台的职位接口。

这个站点的企业页（corp.html）里，"招聘职位"那块是 JS 后加载的，
用 requests 抓 HTML 只能拿到空壳。分析它引用的 corpJob 脚本后发现，
职位数据来自一个 JSON 接口，直接请求接口就能拿到结构化数据。

这种方式比"抓页面再让模型抽"更稳：字段本来就分好了，不用猜。
"""

import re

import requests

from config import HEADERS, TIMEOUT

API_URL = "https://www.ncss.cn/student/jobs/corp/jobs.json"

# 匹配 https://www.ncss.cn/student/jobs/<公司ID>/corp.html
CORP_PATTERN = re.compile(r"/student/jobs/([0-9a-f]+)/corp\.html")


def parse_corp_id(url):
    """从企业页网址里取出公司 ID，不是企业页就返回 None。"""
    match = CORP_PATTERN.search(url)
    return match.group(1) if match else None


def fetch_corp_jobs(corp_id, page_size=50):
    """请求职位接口，自动翻页，返回项目统一的岗位列表。"""
    jobs = []
    page = 1
    headers = dict(HEADERS)
    headers["Referer"] = f"https://www.ncss.cn/student/jobs/{corp_id}/corp.html"

    while True:
        params = {
            "corpId": corp_id,
            "offset": str(page),
            "limit": str(page_size),
        }
        resp = requests.get(API_URL, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        page_data = data.get("data") or {}
        items = page_data.get("list") or []
        if not items:
            break

        for item in items:
            jobs.append(
                {
                    "company": item.get("corpName"),
                    "job_title": item.get("jobName"),
                    "salary": item.get("salary"),
                    "education": item.get("degreeName"),
                    "location": item.get("areaCodeName"),
                }
            )

        total = (page_data.get("pagenation") or {}).get("count", 0)
        if len(jobs) >= total or len(items) < page_size:
            break
        page += 1

    return jobs
