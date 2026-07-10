"""Execute every named SQL analysis and export the results.

Scans sql/*.sql for queries tagged with `-- :name <query_name>` headers,
runs each against data/processed/store.db, and writes results to
reports/analysis/<query_name>.csv. Prints a short preview of each so the
whole analysis suite can be sanity-checked in one run.

Usage:
    python src/run_analysis.py
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
DB_PATH = ROOT / "data" / "processed" / "store.db"
OUT_DIR = ROOT / "reports" / "analysis"

NAME_TAG = re.compile(r"^--\s*:name\s+(\w+)\s*$", re.MULTILINE)

ANALYSIS_FILES = [
    "sales_analysis.sql",
    "product_performance.sql",
    "inventory_health.sql",
    "transfer_recommendations.sql",
    "margin_analysis.sql",
    "sell_through.sql",
]


def named_queries(sql_text: str) -> dict[str, str]:
    """Split a .sql file into {query_name: sql} using -- :name headers."""
    matches = list(NAME_TAG.finditer(sql_text))
    queries: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(sql_text)
        queries[m.group(1)] = sql_text[start:end].strip().rstrip(";")
    return queries


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        for sql_file in ANALYSIS_FILES:
            text = (SQL_DIR / sql_file).read_text(encoding="utf-8")
            for name, query in named_queries(text).items():
                df = pd.read_sql_query(query, con)
                out = OUT_DIR / f"{name}.csv"
                df.to_csv(out, index=False)
                print(f"=== {name}  ({len(df)} rows -> {out.relative_to(ROOT)})")
                with pd.option_context("display.width", 120, "display.max_columns", 20):
                    print(df.head(5).to_string(index=False))
                print()
    finally:
        con.close()


if __name__ == "__main__":
    main()
