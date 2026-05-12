"""Enrich agent — attaches market and macro data to classified items."""
import uuid
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, fetchone, execute
from config.settings import COMPANY_TICKER_MAP, COMMODITY_TICKERS, FRED_SERIES, FRED_API_KEY, ENRICHMENT_CACHE_HOURS

logger = logging.getLogger(__name__)


def get_cached(key: str) -> dict | None:
    row = fetchone(
        "SELECT value_json, expires_at FROM enrichment_cache WHERE key = ?", (key,)
    )
    if not row:
        return None
    if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        return None
    try:
        return json.loads(row["value_json"])
    except Exception:
        return None


def set_cached(key: str, value: dict):
    expires_at = (datetime.utcnow() + timedelta(hours=ENRICHMENT_CACHE_HOURS)).isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO enrichment_cache (key, value_json, cached_at, expires_at)
               VALUES (?, ?, ?, ?)""",
            (key, json.dumps(value), datetime.utcnow().isoformat(), expires_at),
        )


def fetch_stock_data(symbol: str) -> dict | None:
    cache_key = f"stock:{symbol}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if hist.empty:
            return None
        close_prices = hist["Close"].dropna()
        if len(close_prices) < 1:
            return None
        current = float(close_prices.iloc[-1])
        prev = float(close_prices.iloc[-2]) if len(close_prices) > 1 else current
        pct_change = ((current - prev) / prev * 100) if prev else 0
        info = ticker.info or {}
        data = {
            "symbol": symbol,
            "price": round(current, 2),
            "pct_change_1d": round(pct_change, 2),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "USD"),
        }
        set_cached(cache_key, data)
        return data
    except Exception as e:
        logger.debug(f"Stock fetch failed for {symbol}: {e}")
        return None


def fetch_commodities() -> dict:
    cache_key = "commodities:all"
    cached = get_cached(cache_key)
    if cached:
        return cached

    result = {}
    for name, ticker in COMMODITY_TICKERS.items():
        data = fetch_stock_data(ticker)
        if data:
            result[name] = data

    if result:
        set_cached(cache_key, result)
    return result


def fetch_fred_data() -> dict:
    cache_key = "fred:macro"
    cached = get_cached(cache_key)
    if cached:
        return cached

    if not FRED_API_KEY:
        return {}

    result = {}
    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_API_KEY)
        for name, series_id in FRED_SERIES.items():
            try:
                series = fred.get_series(series_id)
                if not series.empty:
                    result[name] = {
                        "value": float(series.iloc[-1]),
                        "date": series.index[-1].strftime("%Y-%m-%d"),
                    }
            except Exception as e:
                logger.debug(f"FRED {series_id} failed: {e}")
    except ImportError:
        logger.debug("fredapi not installed")

    if result:
        set_cached(cache_key, result)
    return result


def enrich_item(classified: dict) -> dict:
    extracted_id = classified.get("extracted_id")
    extracted = fetchone("SELECT * FROM extracted_items WHERE id = ?", (extracted_id,)) or {}

    try:
        entities = json.loads(extracted.get("entities_json", "{}")) if isinstance(extracted.get("entities_json"), str) else {}
    except Exception:
        entities = {}

    enrichment = {}

    companies = entities.get("companies", [])
    stock_data = {}
    for company in companies[:5]:
        ticker = COMPANY_TICKER_MAP.get(company)
        if ticker:
            data = fetch_stock_data(ticker)
            if data:
                stock_data[company] = data
    if stock_data:
        enrichment["stocks"] = stock_data

    enrichment["commodities"] = fetch_commodities()

    fred_data = fetch_fred_data()
    if fred_data:
        enrichment["macro_us"] = fred_data

    return enrichment


def run() -> int:
    pending = fetchall(
        "SELECT ci.* FROM classified_items ci WHERE ci.status = 'pending'"
    )
    enriched = 0

    for item in pending:
        try:
            enrichment_data = enrich_item(item)
            enriched_id = str(uuid.uuid4())
            with get_conn() as conn:
                conn.execute(
                    """INSERT INTO enriched_items (id, classified_id, enrichment_json, enriched_at, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        enriched_id,
                        item["id"],
                        json.dumps(enrichment_data),
                        datetime.utcnow().isoformat(),
                        "pending",
                    ),
                )
                conn.execute(
                    "UPDATE classified_items SET status = 'enriched' WHERE id = ?",
                    (item["id"],),
                )
            enriched += 1
        except Exception as e:
            logger.error(f"Enrich failed for {item['id']}: {e}")

    logger.info(f"[Enrich] Enriched {enriched} items")
    return enriched


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
