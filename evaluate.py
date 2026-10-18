"""用人工标注的标准答案评测抽取质量。

跑法：python evaluate.py

脚本读 data/gold.json 里的标准答案，再从 cache/ 读模型上次的结果，逐字段比对。
所以评测之前要先用 main.py 把样本跑一遍，让缓存里存着结果。

三个指标：
精确率 Precision：模型输出的字段里，有多少是对的。多抽了岗位会拉低它。
召回率 Recall：标准答案的字段里，模型找回了多少。漏抽岗位会拉低它。
F1：两者的调和平均，用来看整体水平。
"""

import json
import os

import cache
from config import FIELDS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_PATH = os.path.join(BASE_DIR, "data", "gold.json")


def load_gold():
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def match_jobs(gold_jobs, pred_jobs):
    """按岗位名称把预测和标准答案对齐。

    返回三样东西：
    matched  对上的 (标准岗位, 预测岗位) 列表
    missed   标准答案里有、但模型没抽到的岗位
    extra    模型多抽出来、标准答案里没有的岗位
    """
    remaining = list(pred_jobs)
    matched = []
    missed = []

    for gold in gold_jobs:
        found = None
        for pred in remaining:
            if pred.get("job_title") == gold.get("job_title"):
                found = pred
                break
        if found is None:
            missed.append(gold)
        else:
            remaining.remove(found)
            matched.append((gold, found))

    return matched, missed, remaining


def compare_fields(gold, pred):
    """逐字段比对，返回正确字段数。两边都是 None 也算对。"""
    return sum(1 for field in FIELDS if gold.get(field) == pred.get(field))


def main():
    gold_pages = load_gold()

    total_correct = 0
    total_gold_fields = 0
    total_pred_fields = 0

    for page in gold_pages:
        url = page["url"]
        gold_jobs = page["jobs"]
        pred_jobs = cache.load(url)

        print("=" * 72)
        print(url)

        if pred_jobs is None:
            print("  缓存里没有这个网址的结果，先用 main.py 跑一遍再评测")
            continue

        matched, missed, extra = match_jobs(gold_jobs, pred_jobs)

        page_correct = 0
        for gold, pred in matched:
            page_correct += compare_fields(gold, pred)
            for field in FIELDS:
                if gold.get(field) != pred.get(field):
                    print(
                        f"  字段不一致 [{gold.get('job_title')}] {field}："
                        f"标准={gold.get(field)!r} 预测={pred.get(field)!r}"
                    )

        total_correct += page_correct
        total_gold_fields += len(gold_jobs) * len(FIELDS)
        total_pred_fields += (len(matched) + len(extra)) * len(FIELDS)

        print(
            f"  标准岗位 {len(gold_jobs)} 个 | 对上 {len(matched)} 个 | "
            f"漏抽 {len(missed)} 个 | 多抽 {len(extra)} 个"
        )
        if missed:
            print("  漏抽的岗位：" + "、".join(str(j.get("job_title")) for j in missed))
        if extra:
            print("  多抽的岗位：" + "、".join(str(j.get("job_title")) for j in extra))

    print()
    print("=" * 72)
    precision = total_correct / total_pred_fields if total_pred_fields else 0
    recall = total_correct / total_gold_fields if total_gold_fields else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    print(f"标准答案字段数：{total_gold_fields}")
    print(f"模型输出字段数：{total_pred_fields}")
    print(f"正确字段数：{total_correct}")
    print(f"精确率 Precision：{precision:.1%}")
    print(f"召回率 Recall：{recall:.1%}")
    print(f"F1：{f1:.1%}")


if __name__ == "__main__":
    main()
