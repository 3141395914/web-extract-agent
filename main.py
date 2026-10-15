"""命令行入口：把网页链接交给程序，结果存成 CSV。

用法：
    python main.py https://example.com/job/1 https://example.com/job/2
"""

import csv
import os
import sys

from config import DEFAULT_URLS, FIELDS
from extract import extract_jobs_checked
from fetch import fetch_page_text

OUTPUT_DIR = "output"


def process(url):
    """处理单个网址，返回这个页面里的岗位列表。"""
    print(f"[1/3] 抓取网页：{url}")
    page_text = fetch_page_text(url)
    print(f"      正文长度 {len(page_text)} 字符")

    print("[2/3] 调用模型抽取岗位，并核对每个字段有没有依据...")
    jobs, retries, bad_fields = extract_jobs_checked(page_text)

    if bad_fields:
        names = "、".join(f"岗位 {i + 1} 的 {name}" for i, name, _ in bad_fields)
        print(f"      重试 {retries} 次后，这些字段仍没在原文里找到依据：{names}")
    elif retries:
        print(f"      重试 {retries} 次后全部通过核对")
    else:
        print("      一次通过核对，所有字段都能在原文里找到依据")

    print(f"[3/3] 抽取完成，这个页面共 {len(jobs)} 个岗位")
    for job in jobs:
        job["url"] = url  # 每个岗位都记下它来自哪个页面
    return jobs


def save_csv(records, path):
    """把结果写成 CSV，列的顺序跟 config.py 里定义的字段一致。"""
    columns = ["url"] + list(FIELDS.keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        # extrasaction="ignore"：模型多返回了用不上的字段时忽略，不要报错
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow(row)


def main():
    urls = sys.argv[1:]
    if not urls:
        urls = DEFAULT_URLS
        print("没有传入网址，使用 config.py 里配置的示例链接")
        print("想换网址就在命令行里写：python main.py <网址1> <网址2> ...\n")

    records = []
    for url in urls:
        try:
            jobs = process(url)
            records.extend(jobs)
            for job in jobs:
                print(f"      {job}")
        except Exception as e:
            print(f"      这一条失败了：{type(e).__name__}: {e}")

    if not records:
        print("没有任何一条成功，没有生成文件")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "result.csv")
    save_csv(records, path)
    print(f"\n共 {len(records)} 个岗位，已保存到 {path}")


if __name__ == "__main__":
    main()
