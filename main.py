"""命令行入口：把网页链接交给程序，结果存成 CSV。

用法：
    python main.py https://example.com/job/1 https://example.com/job/2
"""

import csv
import os
import sys

from config import FIELDS
from extract import extract_fields
from fetch import fetch_page_text

OUTPUT_DIR = "output"


def process(url):
    """处理单个网址，返回一条记录。"""
    print(f"[1/3] 抓取网页：{url}")
    page_text = fetch_page_text(url)
    print(f"      正文长度 {len(page_text)} 字符")

    print("[2/3] 调用模型抽取字段...")
    record = extract_fields(page_text)

    print("[3/3] 抽取完成")
    return record


def save_csv(records, path):
    """把结果写成 CSV，列的顺序跟 config.py 里定义的字段一致。"""
    columns = ["url"] + list(FIELDS.keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in records:
            writer.writerow(row)


def main():
    urls = sys.argv[1:]
    if not urls:
        print("用法：python main.py <网址1> <网址2> ...")
        return

    records = []
    for url in urls:
        try:
            record = process(url)
            record["url"] = url
            records.append(record)
            print(f"      抽取结果：{record}")
        except Exception as e:
            print(f"      这一条失败了：{type(e).__name__}: {e}")

    if not records:
        print("没有任何一条成功，没有生成文件")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "result.csv")
    save_csv(records, path)
    print(f"\n共 {len(records)} 条结果，已保存到 {path}")


if __name__ == "__main__":
    main()
