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

GEMINI_API_KEY = os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.getenv("AI_INTEGRATIONS_GEMINI_BASE_URL", "")
GEMINI_MODEL = "gemini-2.5-flash"

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "newslens/1.0")

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./newslens.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")

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
