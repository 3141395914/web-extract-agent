"""第二步：把网页正文交给 DeepSeek，抽成结构化字段。"""

import json
import os
import time

import requests
from dotenv import load_dotenv

from config import API_URL, FIELDS, MAX_API_RETRY, MAX_RETRY, MODEL_NAME, TIMEOUT
from verify import find_bad_fields

load_dotenv()  # 从 .env 文件里读密钥


def build_prompt(page_text, hint=None):
    """拼出要发给模型的提示词：告诉它抽哪些字段、按什么格式返回。

    hint 是重试时加的一段话，用来告诉模型上次哪些字段填得不对。
    """
    field_lines = "\n".join(f"- {name}: {desc}" for name, desc in FIELDS.items())
    parts = [
        "你是一个网页信息抽取助手。下面是一段招聘网页的正文。"
        "里面可能同时列出了好几个岗位，请把每一个岗位都抽出来，不要只抽第一个。\n\n"
        f"每个岗位需要抽取的字段：\n{field_lines}\n\n"
        "请以 json 格式返回，格式固定为：\n"
        '{"jobs": [{"字段名": "值"}, {"字段名": "值"}]}\n'
        "只返回 json，不要任何解释。原文里没有的字段填 null，不要编造。"
        "如果整页只招一个岗位，jobs 里就只有一项。"
    ]
    if hint:
        parts.append(hint)
    parts.append(f"网页正文：\n{page_text}")
    return "\n\n".join(parts)


def call_model(prompt, max_try=MAX_API_RETRY):
    """调用 DeepSeek 接口，返回模型回复的文本。

    接口偶尔会返回 5xx 或者连接中断，所以这里做几次退避重试：
    第一次等 1 秒，第二次等 2 秒。等的时间一次比一次长，避免对方刚出问题
    我们就猛敲，反而更容易被限流。
    """
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

    last_error = None
    for attempt in range(max_try):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
            if resp.status_code >= 500:
                raise requests.HTTPError(f"{resp.status_code} {resp.reason}")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, ValueError, KeyError) as e:
            last_error = e
            if attempt < max_try - 1:
                wait = 2 ** attempt
                print(f"      接口调用失败（{e}），{wait} 秒后重试")
                time.sleep(wait)

    raise last_error


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


def extract_jobs(page_text, hint=None):
    """抽取主流程：拼提示词 -> 调模型 -> 解析结果，返回岗位列表。"""
    prompt = build_prompt(page_text, hint)
    reply = call_model(prompt)
    data = parse_json(reply)

    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        # 模型没按约定的格式返回时退一步，把它当成只有一个岗位
        jobs = [data]

    # 没有岗位名称的记录不算一个岗位。页面里根本没有岗位时，
    # 模型有时会硬返回一条只有公司名的空记录，这种要丢掉。
    jobs = [job for job in jobs if job.get("job_title")]
    return jobs


def build_hint(bad_fields):
    """把没通过核对的字段整理成一段话，重试时一起发给模型。"""
    lines = [
        f"岗位 {index + 1} 的 {name} 字段，上次填的是「{value}」"
        for index, name, value in bad_fields
    ]
    return (
        "上一次抽取时，下面这些字段填的内容在原文里找不到依据：\n"
        + "\n".join(lines)
        + "\n请重新仔细核对原文，只填原文中确实出现过的内容，尽量照抄原文的原话；"
        "如果原文确实没有，就填 null。"
    )


def extract_jobs_checked(page_text, max_retry=MAX_RETRY):
    """抽取、核对、不过关就重抽，最多重试 max_retry 次。

    返回 (岗位列表, 实际重试次数, 最后仍未通过核对的字段)。
    重试用完还有问题的字段不会丢弃，只是记录下来，让人知道哪条没核实过。
    """
    hint = None
    jobs = []
    bad_fields = []

    for attempt in range(max_retry + 1):
        jobs = extract_jobs(page_text, hint)
        bad_fields = find_bad_fields(jobs, page_text)
        if not bad_fields:
            return jobs, attempt, []

        print(f"      第 {attempt + 1} 次抽取，有 {len(bad_fields)} 个字段在原文里找不到依据")
        if attempt < max_retry:
            hint = build_hint(bad_fields)

    return jobs, max_retry, bad_fields
