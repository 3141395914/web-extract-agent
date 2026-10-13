"""第一步：把网页抓下来，并洗成干净的正文文本。"""

import requests
from bs4 import BeautifulSoup

from config import HEADERS, MAX_CHARS, TIMEOUT


def fetch_html(url):
    """抓取网页，返回 HTML 字符串。"""
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()  # 状态码不是 200 就直接抛异常
    resp.encoding = resp.apparent_encoding  # 让中文页面不乱码
    return resp.text


def html_to_text(html):
    """把 HTML 里的正文抽出来，去掉脚本、样式和多余空行。"""
    soup = BeautifulSoup(html, "html.parser")

    # 脚本和样式对我们没用，先整块删掉
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]  # 丢掉空行
    return "\n".join(lines)[:MAX_CHARS]


def fetch_page_text(url):
    """抓取加清洗，一步到位。"""
    return html_to_text(fetch_html(url))
