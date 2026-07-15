"""Load the cleaned CSVs into a SQLite database.

Creates data/processed/store.db from sql/create_tables.sql and loads the
three cleaned tables. The .db file is git-ignored; anyone can rebuild it
with: python src/generate_sample_data.py && python src/clean_data.py &&
python src/load_db.py

Usage:
    python src/load_db.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SCHEMA = ROOT / "sql" / "create_tables.sql"
DB_PATH = PROCESSED / "store.db"

TABLES = {
    "products": "products_clean.csv",
    "sales": "sales_clean.csv",
    "inventory": "inventory_clean.csv",
}


def main(db_path: Path = DB_PATH) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        for table, csv_name in TABLES.items():
            df = pd.read_csv(PROCESSED / csv_name)
            df.to_sql(table, con, if_exists="append", index=False)
            n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table:<10} {n:>7,} rows")
        con.commit()
    finally:
        con.close()
    print(f"database -> {db_path}")


if __name__ == "__main__":
    main()
