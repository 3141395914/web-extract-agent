"""按关键词抓取国家大学生就业服务平台的职位列表。

用法：
    python crawl_list.py                         抓全部职位
    python crawl_list.py Python                  按关键词 Python 抓
    python crawl_list.py "https://..."           直接粘贴浏览器里的完整接口地址
    python crawl_list.py Python 3                关键词 Python，最多抓 3 页

结果保存到 output/result_list.csv，格式和 main.py 输出的 CSV 一致。
"""

import csv
import os
import sys
import time
from urllib.parse import parse_qs, urlparse

import requests

from config import HEADERS, TIMEOUT

API_URL = "https://www.ncss.cn/student/jobs/jobslist/ajax/"
DETAIL_URL = "https://www.ncss.cn/student/jobs/{job_id}/detail.html"

# 和页面请求保持一致的默认参数
DEFAULT_PARAMS = {
    "jobType": "",
    "areaCode": "",
    "jobName": "",
    "monthPay": "",
    "industrySectors": "",
    "property": "",
    "categoryCode": "",
    "memberLevel": "",
    "recruitType": "",
    "offset": "1",
    "limit": "10",
    "keyUnits": "",
    "degreeCode": "",
    "sourcesName": "0",
    "sourcesType": "",
}


def format_salary(item):
    """把接口里的最低/最高月薪拼成一段文字。"""
    low = item.get("lowMonthPay")
    high = item.get("highMonthPay")
    if not low and not high:
        # 接口没给薪资时，页面上显示的是"面议"
        return "面议"
    # 接口用 99 表示"薪资面议"，不是一个真的数字
    if high and high >= 99:
        return "面议"
    if low == high:
        return f"{low}K/月"
    return f"{low}-{high}K/月"


def parse_url_params(url):
    """从浏览器复制的完整接口地址里取出查询参数。"""
    query = urlparse(url).query
    params = {
        key: value[0]
        for key, value in parse_qs(query, keep_blank_values=True).items()
        if key != "_"
    }
    params.setdefault("limit", "10")
    return params


def fetch_page(base_params, page, headers, retries=3):
    """抓一页，返回接口里的 data 部分。

    接口偶尔会返回空的 data，或者请求过快被限制，这里重试几次。
    """
    params = dict(base_params)
    params["offset"] = str(page)

    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json().get("data")
            if data:
                return data
        except requests.RequestException as e:
            print(f"    第 {page} 页请求失败：{e}")
        time.sleep(1)

    return {}


def main():
    first_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    if first_arg.startswith("http"):
        base_params = parse_url_params(first_arg)
        print("从网址解析参数：", {k: v for k, v in base_params.items() if v})
    else:
        base_params = dict(DEFAULT_PARAMS)
        base_params["jobName"] = first_arg

    headers = dict(HEADERS)
    headers["Referer"] = "https://www.ncss.cn/student/jobs/index.html"

    first = fetch_page(base_params, 1, headers)
    page_info = first.get("pagenation") or {}
    total_pages = page_info.get("total", 1)
    count = page_info.get("count", 0)
    print(f"共 {count} 个职位，{total_pages} 页")

    if max_pages:
        total_pages = min(total_pages, max_pages)
        print(f"本次最多抓 {total_pages} 页")

    rows = []
    seen = set()

    for page in range(1, total_pages + 1):
        data = first if page == 1 else fetch_page(base_params, page, headers)
        items = data.get("list") or []
        if not items:
            print(f"  第 {page} 页没有数据，跳过")
            continue

        for item in items:
            job_id = item.get("jobId")
            if job_id in seen:
                continue
            seen.add(job_id)
            rows.append(
                {
                    "url": DETAIL_URL.format(job_id=job_id),
                    "company": item.get("recName"),
                    "job_title": item.get("jobName"),
                    "salary": format_salary(item),
                    "education": item.get("degreeName"),
                    "location": item.get("areaCodeName"),
                }
            )
        print(f"  第 {page} 页完成，累计 {len(rows)} 条")
        time.sleep(0.5)

    os.makedirs("output", exist_ok=True)
    # 文件名带时间戳，避免重跑时覆盖上次抓到的数据
    stamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("output", f"jobs_{stamp}.csv")
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["url", "company", "job_title", "salary", "education", "location"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n共 {len(rows)} 条，已保存到 {output_path}")


if __name__ == "__main__":
    main()
