"""第二步：把网页正文交给 DeepSeek，抽成结构化字段。"""

import json
import os

import requests
from dotenv import load_dotenv

from config import API_URL, FIELDS, MODEL_NAME, TIMEOUT

load_dotenv()  # 从 .env 文件里读密钥


def build_prompt(page_text):
    """拼出要发给模型的提示词：告诉它抽哪些字段、按什么格式返回。"""
    field_lines = "\n".join(f"- {name}: {desc}" for name, desc in FIELDS.items())
    return (
        "你是一个网页信息抽取助手。下面是一段网页正文，"
        "请从中抽取指定字段，并以 json 格式返回，只返回 json，不要任何解释。\n\n"
        f"需要抽取的字段：\n{field_lines}\n\n"
        f"网页正文：\n{page_text}"
    )


def call_model(prompt):
    """调用 DeepSeek 接口，返回模型回复的文本。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY，请检查 .env 文件是否配好")

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},  # 要求模型必须返回 json
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_json(reply):
    """把模型返回的文本转成字典。

    实测下来，模型偶尔会在 json 后面多写一段解释，直接解析整段文本会报
    "Extra data" 的错误。所以这里不整段解析，而是从第一个左括号开始，
    只取第一个完整的 json 对象。
    """
    text = reply.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json\n", "", 1)

    start = text.find("{")
    if start == -1:
        raise ValueError(f"返回内容里没有 json 对象：{text[:80]}")
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def extract_fields(page_text):
    """抽取主流程：拼提示词 -> 调模型 -> 解析结果。"""
    prompt = build_prompt(page_text)
    reply = call_model(prompt)
    return parse_json(reply)
