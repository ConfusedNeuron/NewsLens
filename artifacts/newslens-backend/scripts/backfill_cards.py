#!/usr/bin/env python3
"""
Backfill `market_data` and `time_horizon` on cards created before those columns existed.

Nothing is re-generated and no LLM is called. Both values were already produced by the
pipeline and stored on the corresponding `enriched_items` row — the enrichment payload
under the top-level keys, and the horizon inside the `_analysis` blob. The format agent
simply never carried them across to the card.

Safe to run repeatedly: only rows where the column is still NULL are touched.

    python scripts/backfill_cards.py            # show what would change
    python scripts/backfill_cards.py --apply    # write it
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import get_conn, fetchall
from agents.format_agent import _normalize_horizon


def collect() -> list[dict]:
    """Find cards missing the new fields whose enriched row can supply them."""
    rows = fetchall(
        """SELECT c.id AS card_id,
                  c.time_horizon AS card_horizon,
                  c.market_data  AS card_market,
                  e.enrichment_json AS enrichment
           FROM cards c
           JOIN enriched_items e ON e.id = c.enriched_id
           WHERE c.market_data IS NULL OR c.time_horizon IS NULL"""
    )

    updates = []
    for row in rows:
        try:
            payload = json.loads(row["enrichment"] or "{}")
        except Exception:
            continue

        analysis = payload.get("_analysis") or {}
        market = {k: v for k, v in payload.items() if k != "_analysis"}

        update = {"card_id": row["card_id"]}
        if row["card_market"] is None and market:
            update["market_data"] = json.dumps(market)
        if row["card_horizon"] is None and analysis.get("time_horizon"):
            update["time_horizon"] = _normalize_horizon(analysis["time_horizon"])

        if len(update) > 1:
            updates.append(update)

    return updates


def apply(updates: list[dict]) -> int:
    written = 0
    with get_conn() as conn:
        for u in updates:
            fields = [k for k in ("market_data", "time_horizon") if k in u]
            assignments = ", ".join(f"{f} = ?" for f in fields)
            conn.execute(
                f"UPDATE cards SET {assignments} WHERE id = ?",
                tuple(u[f] for f in fields) + (u["card_id"],),
            )
            written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the changes")
    args = parser.parse_args()

    updates = collect()
    if not updates:
        print("Nothing to backfill — every card already has market_data and time_horizon.")
        return 0

    with_market = sum(1 for u in updates if "market_data" in u)
    with_horizon = sum(1 for u in updates if "time_horizon" in u)
    print(f"{len(updates)} card(s) can be backfilled "
          f"({with_market} market_data, {with_horizon} time_horizon).")

    if not args.apply:
        print("\nDry run. Re-run with --apply to write.")
        return 0

    print(f"Updated {apply(updates)} cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
