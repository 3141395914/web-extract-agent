"""校验器的自测。

跑法：在项目根目录执行 python tests/test_verify.py

这里用一段假造的网页正文，故意混进几个原文里没有的值，看校验器能不能抓出来。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verify import check_value, find_bad_fields, normalize

PAGE = """
洛阳智达石化工程有限公司2027年招聘简章
招聘岗位：工艺设计师、管道设计师
学历要求：本科及以上
薪资：5000-6500元/月
工作地点：洛阳
"""

# (值, 期望能不能通过, 说明)
CASES = [
    ("洛阳智达石化工程有限公司", True, "公司名照抄原文"),
    ("5000-6500元/月", True, "薪资照抄原文"),
    ("本科及以上", True, "学历照抄原文"),
    ("洛阳", True, "地点照抄原文"),
    ("9999-12000元/月", False, "薪资金额是编的"),
    ("硕士及以上", False, "原文没有这个学历要求"),
    ("郑州大学", False, "原文没有这个学校"),
    (None, True, "没抽到内容，允许"),
    ("", True, "空字符串，允许"),
]


def main():
    page_norm = normalize(PAGE)
    failed = 0

    for value, expected, desc in CASES:
        got = check_value(value, page_norm)
        mark = "正确" if got == expected else "错误"
        if got != expected:
            failed += 1
        print(f"[{mark}] {desc}：值={value!r} 期望={expected} 实际={got}")

    # 再测一次整体流程：两个岗位里各埋一个假值
    jobs = [
        {"company": "洛阳智达石化工程有限公司", "job_title": "工艺设计师", "salary": "5000-6500元/月"},
        {"company": "洛阳智达石化工程有限公司", "job_title": "架构师", "salary": "20000元/月"},
    ]
    bad = find_bad_fields(jobs, PAGE)
    print()
    print("整页核对找出的问题字段：")
    for index, name, value in bad:
        print(f"  岗位 {index + 1} 的 {name} = {value!r}")

    print()
    print("逐条用例失败数：", failed)
    print("整页核对抓到的假值数：", len(bad))


if __name__ == "__main__":
    main()
