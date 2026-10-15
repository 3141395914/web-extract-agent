"""第三步：核对抽出来的字段在原文里有没有依据。

模型会编。它可能报出一个原文里根本不存在的薪资，或者把原文的「本科」
改写成「本科及以上」。所以抽完不能直接信，要拿每个字段的值回原文核对一遍。

核对办法很朴素：把字段值和原文都去掉空格标点、统一小写，然后检查两样东西，
一是值里的数字是不是在原文出现过，二是值里最长的汉字片段是不是在原文出现过。
两样都对得上才算通过。
"""

import re

from config import FIELDS

# 归一化时要去掉的空白和标点
PUNCT_CHARS = " \t\r\n\u3000，。、；：？！（）()[]【】-—~～/\\|·．.,;:!?\"'`“”‘’"
PUNCT = re.compile("[" + re.escape(PUNCT_CHARS) + "]+")
NUMBER = re.compile(r"\d+")
HAN = re.compile(r"[\u4e00-\u9fff]+")

# 汉字片段短于这个长度就不检查了，太短的词到处都是，查了也没意义
MIN_HAN_LEN = 3


def normalize(text):
    """去掉空白和标点，转成小写，方便做包含判断。"""
    return PUNCT.sub("", str(text).lower())


def check_value(value, page_norm):
    """检查一个字段值能不能在原文里找到依据，通过返回 True。"""
    if value is None or value == "":
        # 没抽到内容是允许的，模型说不确定总比编一个强
        return True

    value_text = str(value)

    # 数字一个都不能是原文里没有的
    for number in NUMBER.findall(value_text):
        if number not in page_norm:
            return False

    # 最长的汉字片段要能在原文里找到
    pieces = HAN.findall(value_text)
    if pieces:
        longest = max(pieces, key=len)
        if len(longest) >= MIN_HAN_LEN and longest not in page_norm:
            return False

    return True


def find_bad_fields(jobs, page_text):
    """找出所有没通过核对的字段。

    返回 [(岗位序号, 字段名, 上次抽出来的值), ...]，岗位序号从 0 开始。
    """
    page_norm = normalize(page_text)
    bad = []
    for index, job in enumerate(jobs):
        for field in FIELDS:
            if field in job and not check_value(job[field], page_norm):
                bad.append((index, field, job[field]))
    return bad
