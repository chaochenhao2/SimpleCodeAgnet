import os
from dotenv import load_dotenv
from openai import OpenAI

# ================== 配置加载 ==================
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
API_MODEL = os.getenv("API_MODEL")

if not all([API_KEY, API_BASE_URL, API_MODEL]):
    raise ValueError("请在 .env 文件中设置 API_KEY, API_BASE_URL, API_MODEL")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ================== 会话存储目录 ==================
from pathlib import Path
SCRIPT_DIR = Path(__file__).parent
SESSION_DIR = SCRIPT_DIR / ".MY_CODE_AGENT"
SESSION_DIR.mkdir(exist_ok=True)
