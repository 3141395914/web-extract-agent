"""项目的全部配置都放在这里，想换抽取场景只改这个文件。"""

# DeepSeek 的接口地址（它兼容 OpenAI 的接口格式）
API_URL = "https://api.deepseek.com/chat/completions"

# 使用的模型名，deepseek-chat 是便宜的那个
MODEL_NAME = "deepseek-chat"

# 要抽取的字段。键是字段名，值是给模型看的说明。
# 想换成别的场景，把这里改掉就行，别的代码不用动。
FIELDS = {
    "company": "招聘公司的名称",
    "job_title": "岗位名称",
    "salary": "薪资范围，原文没有就填 null",
    "education": "学历要求，原文没有就填 null",
    "location": "工作城市，原文没有就填 null",
}

# 抓网页时用的请求头，让服务器把我们当成普通浏览器
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# 网页正文太长会浪费 token，这里截断
MAX_CHARS = 6000

# 网络请求的超时时间（秒）
TIMEOUT = 30

# 没有在命令行里传网址时，默认跑这几条，方便直接点"运行"按钮
DEFAULT_URLS = [
    "https://job.haut.edu.cn/module/position_brief_detail/id-115108/nid-8782",
]
