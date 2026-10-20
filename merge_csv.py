"""合并 output 目录下的所有 jobs_*.csv，并按 url 去重。

跑法：
    python merge_csv.py

输出 output/all_jobs.csv。
"""

import glob
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def main():
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "jobs_*.csv")))
    if not files:
        print("没有找到 jobs_*.csv，先跑 crawl_list.py")
        return

    frames = []
    for path in files:
        df = pd.read_csv(path)
        print(f"  {os.path.basename(path)}：{len(df)} 条")
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    total = len(merged)
    print(f"\n合并后：{total} 条")

    # 同一个职位在不同分类里可能重复出现，按 url 去重
    merged = merged.drop_duplicates(subset=["url"])
    print(f"按 url 去重后：{len(merged)} 条，删掉 {total - len(merged)} 条重复")

    out_path = os.path.join(OUTPUT_DIR, "all_jobs.csv")
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"已保存到 {out_path}")


if __name__ == "__main__":
    main()
