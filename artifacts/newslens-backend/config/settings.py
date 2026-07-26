import os
from dotenv import load_dotenv

load_dotenv()

PIPELINE_INTERVAL_HOURS = int(os.getenv("PIPELINE_INTERVAL_HOURS", "6"))
MAX_ARTICLES_PER_FEED = 20
REDDIT_SCORE_THRESHOLD = 50
DEDUP_SIMILARITY_THRESHOLD = 0.85
IMPORTANCE_SCORE_THRESHOLD = 0.3
LLM_MAX_CONCURRENT = 10
LLM_CALL_DELAY_SECONDS = 0.5
ENRICHMENT_CACHE_HOURS = 4
LANGUAGES_ALLOWED = ["en", "hi"]

# ── LLM Provider — OpenAI-compatible, swap base_url to switch provider ────
#
# All providers below use the same OpenAI Python SDK. Only the key + base_url changes.
# Set both in your .env file:
#   COMMANDCODE_API_KEY=<your key>
#   LLM_BASE_URL=<provider url>        ← optional, overrides the default below
#
# ┌─────────────────────┬──────────────────────────────────────────┬───────────────┐
# │ Provider            │ Base URL                                 │ Free tier?    │
# ├─────────────────────┼──────────────────────────────────────────┼───────────────┤
# │ NVIDIA NIM          │ https://integrate.api.nvidia.com/v1      │ $1 free credit│
# │ OpenRouter          │ https://openrouter.ai/api/v1             │ :free models  │
# │ CommandCode         │ https://api.commandcode.ai/provider/v1   │ Pro plan only │
# │ Together AI         │ https://api.together.xyz/v1              │ $25 free      │
# │ Groq                │ https://api.groq.com/openai/v1           │ Free (fast)   │
# └─────────────────────┴──────────────────────────────────────────┴───────────────┘
#
COMMANDCODE_API_KEY  = os.getenv("COMMANDCODE_API_KEY", "")
COMMANDCODE_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://integrate.api.nvidia.com/v1",  # ← default: NVIDIA NIM
)

# ── Active model ──────────────────────────────────────────────────────────
#
# NVIDIA NIM models (use with https://integrate.api.nvidia.com/v1):
# NOTE: NIM model IDs are case-sensitive and must match exactly.
# Run  python testapi.py --list-models  to get the exact strings for your account.
#
# ── Verified NVIDIA NIM model IDs (from --list-models output) ────────────
# ACTIVE_MODEL = "minimaxai/minimax-m2.7"                    # MiniMax M2.7 230B ← default
# ACTIVE_MODEL = "deepseek-ai/deepseek-v4-pro"             # DeepSeek V4 Pro
ACTIVE_MODEL = "deepseek-ai/deepseek-v4-flash"           # DeepSeek V4 Flash (faster)
# ACTIVE_MODEL = "moonshotai/kimi-k2.6"                    # Kimi K2.6
# ACTIVE_MODEL = "z-ai/glm-5.1"                            # GLM-5.1
# ACTIVE_MODEL = "meta/llama-3.3-70b-instruct"             # Llama 3.3 70B
# ACTIVE_MODEL = "meta/llama-4-maverick-17b-128e-instruct" # Llama 4 Maverick
# ACTIVE_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1" # NVIDIA flagship (253B)
# ACTIVE_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"  # Nemotron Super 49B
# ACTIVE_MODEL = "mistralai/mistral-large-3-675b-instruct-2512"  # Mistral Large 3
# ACTIVE_MODEL = "mistralai/mistral-7b-instruct-v0.3"      # Mistral 7B (fastest/cheapest)
# ACTIVE_MODEL = "qwen/qwen3.5-397b-a17b"                  # Qwen 3.5 397B
# ACTIVE_MODEL = "qwen/qwen3-coder-480b-a35b-instruct"     # Qwen Coder 480B
# ACTIVE_MODEL = "openai/gpt-oss-120b"                     # GPT OSS 120B
#
# OpenRouter free models (switch LLM_BASE_URL to https://openrouter.ai/api/v1):
# ACTIVE_MODEL = "deepseek/deepseek-r1:free"
# ACTIVE_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
#
# Groq free tier (switch LLM_BASE_URL to https://api.groq.com/openai/v1):
# ACTIVE_MODEL = "llama-3.3-70b-versatile"
# ACTIVE_MODEL = "deepseek-r1-distill-llama-70b"
# ─────────────────────────────────────────────────────────────────────────

# Legacy Gemini config (kept in case Replit env vars are still present)
GEMINI_API_KEY  = os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.getenv("AI_INTEGRATIONS_GEMINI_BASE_URL", "")
GEMINI_MODEL    = "gemini-2.5-flash"

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "newslens/1.0")

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./newslens.db")
if DATABASE_URL.startswith("sqlite:///"):
    DB_PATH = DATABASE_URL[len("sqlite:///"):]
else:
    DB_PATH = "./newslens.db"

PORT = int(os.getenv("PORT", "8000"))

SOURCE_CREDIBILITY_WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}

COMPANY_TICKER_MAP = {
    "Reliance": "RELIANCE.NS",
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Tata Consultancy Services": "TCS.NS",
    "Infosys": "INFY",
    "HDFC Bank": "HDB",
    "ICICI Bank": "IBN",
    "Wipro": "WIT",
    "Apple": "AAPL",
    "Google": "GOOGL",
    "Alphabet": "GOOGL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Meta": "META",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "OpenAI": None,
    "Anthropic": None,
    "Samsung": "005930.KS",
    "TSMC": "TSM",
    "Alibaba": "BABA",
    "Tencent": "TCEHY",
    "Baidu": "BIDU",
    "Adani": "ADANIENT.NS",
    "SBI": "SBIN.NS",
    "State Bank of India": "SBIN.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
}

COMMODITY_TICKERS = {
    "crude_oil": "CL=F",
    "gold": "GC=F",
    "usd_inr": "USDINR=X",
    "usd_cny": "CNY=X",
    "silver": "SI=F",
}

FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "us_cpi": "CPIAUCSL",
    "us_gdp": "GDP",
    "us_unemployment": "UNRATE",
}
