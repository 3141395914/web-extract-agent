"""把抽取结果存到本地。

同一个网址跑第二次时就不用再调模型了，省时间也省钱。
"""

import hashlib
import json
import os

# __file__ 是当前这个文件的路径，取它的上一级就是项目根目录。
# 这样不管你在哪个目录下运行程序，缓存都固定建在项目里，不会跑丢。
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")


def url_to_filename(url):
    """网址里有斜杠冒号，不能直接当文件名，先算成一个哈希当文件名。"""
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, digest + ".json")


def load(url):
    """有缓存就返回岗位列表，没有就返回 None。"""
    path = url_to_filename(url)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("jobs", [])


def save(url, jobs):
    """把抽取结果写进缓存文件。"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = url_to_filename(url)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"url": url, "jobs": jobs}, f, ensure_ascii=False, indent=2)
