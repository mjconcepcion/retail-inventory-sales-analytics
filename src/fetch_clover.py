"""Pull real sales and inventory data from the Clover REST API.

Reads per-store credentials from a git-ignored `.env` (see `.env.example`),
walks each store's order history in monthly windows, and normalizes
everything into the pipeline's canonical schema:

    data/private/<YYYY-MM-DD>/products.csv
    data/private/<YYYY-MM-DD>/sales.csv
    data/private/<YYYY-MM-DD>/inventory.csv   (snapshot as of the pull)

Nothing under data/private/ is ever committed. The cleaned public dataset
in data/raw/ is synthetic; this module exists so the same pipeline can be
validated against real business data locally.

Known gaps in what Clover exposes (documented, not hidden):
  * No historical inventory — item_stocks is current-state only, so each
    pull produces one snapshot; history accumulates as you keep pulling.
  * days_in_stock / reorder_level are not Clover concepts; left blank.
  * artist/title are parsed from the item name on a best-effort
    "Artist - Title" split; unsplittable names land in `title` whole.

Usage:
    python src/fetch_clover.py --check              # verify tokens work
    python src/fetch_clover.py --since 2024-01-01   # full pull
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
PRIVATE = ROOT / "data" / "private"
BASE = "https://api.clover.com/v3/merchants"

PAGE_LIMIT = 1000
REQUEST_PAUSE_S = 0.15  # stay well under Clover's per-token rate limit


def load_env() -> list[dict]:
    """Parse .env into a list of store configs. No external dependency."""
    if not ENV_PATH.exists():
        sys.exit("No .env found. Copy .env.example to .env and fill in tokens.")
    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()

    stores = []
    for n in range(1, 10):
        mid = values.get(f"CLOVER_STORE{n}_MID", "")
        token = values.get(f"CLOVER_STORE{n}_TOKEN", "")
        name = values.get(f"CLOVER_STORE{n}_NAME", f"Store {n}")
        if mid and token and not mid.startswith("X") and not token.startswith("0000"):
            stores.append({"name": name, "mid": mid, "token": token})
    if not stores:
        sys.exit("No configured stores in .env (placeholders don't count).")
    return stores


def get(store: dict, path: str, params: dict | None = None) -> dict:
    resp = requests.get(
        f"{BASE}/{store['mid']}/{path}",
        headers={"Authorization": f"Bearer {store['token']}"},
        params=params or {},
        timeout=60,
    )
    resp.raise_for_status()
    time.sleep(REQUEST_PAUSE_S)
    return resp.json()


def paged(store: dict, path: str, params: dict | None = None):
    """Yield elements across offset pages."""
    offset = 0
    while True:
        page = get(store, path, {**(params or {}), "limit": PAGE_LIMIT, "offset": offset})
        elements = page.get("elements", [])
        yield from elements
        if len(elements) < PAGE_LIMIT:
            return
        offset += PAGE_LIMIT


def month_windows(since: date):
    """(start_ms, end_ms) windows from `since` to now, one per month."""
    cursor = since
    today = datetime.now(timezone.utc).date()
    while cursor <= today:
        nxt = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
        start = datetime(cursor.year, cursor.month, cursor.day, tzinfo=timezone.utc)
        end = datetime(min(nxt, today + timedelta(days=1)).year,
                       min(nxt, today + timedelta(days=1)).month,
                       min(nxt, today + timedelta(days=1)).day, tzinfo=timezone.utc)
        yield int(start.timestamp() * 1000), int(end.timestamp() * 1000)
        cursor = nxt


def cents(v) -> float | None:
    return round(v / 100.0, 2) if isinstance(v, (int, float)) else None


def split_name(name: str) -> tuple[str, str]:
    """Best-effort 'Artist - Title' split; else everything is the title."""
    for sep in (" - ", " – ", " — "):
        if sep in name:
            artist, _, title = name.partition(sep)
            return artist.strip(), title.strip()
    return "", name.strip()


def fetch_products(store: dict) -> pd.DataFrame:
    rows = []
    for item in paged(store, "items", {"expand": "categories"}):
        artist, title = split_name(item.get("name", ""))
        categories = [c.get("name", "") for c in item.get("categories", {}).get("elements", [])]
        rows.append({
            "product_id": item["id"],
            "sku": item.get("sku") or item.get("code"),
            "artist": artist,
            "title": title,
            "format": "",                      # not a Clover concept
            "genre": categories[0] if categories else "",
            "condition": "",                   # not a Clover concept
            "cost": cents(item.get("cost")),
            "price": cents(item.get("price")),
            "release_year": None,
        })
    return pd.DataFrame(rows)


def fetch_sales(store: dict, since: date) -> pd.DataFrame:
    rows = []
    for start_ms, end_ms in month_windows(since):
        params = {
            "filter": [f"createdTime>={start_ms}", f"createdTime<{end_ms}"],
            "expand": "lineItems",
        }
        for order in paged(store, "orders", params):
            created = datetime.fromtimestamp(order["createdTime"] / 1000, tz=timezone.utc)
            for li in order.get("lineItems", {}).get("elements", []):
                discounts = sum(
                    -d.get("amount", 0) if d.get("amount", 0) < 0 else d.get("amount", 0)
                    for d in li.get("discounts", {}).get("elements", [])
                )
                rows.append({
                    "sale_id": li["id"],
                    "sale_date": created.date().isoformat(),
                    "location": store["name"],
                    "product_id": (li.get("item") or {}).get("id"),
                    "quantity": li.get("unitQty", 1) or 1,
                    "unit_price": cents(li.get("price")),
                    "discount": cents(discounts) or 0.0,
                })
        print(f"  {store['name']}: through {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).date()} "
              f"({len(rows):,} line items)")
    return pd.DataFrame(rows)


def fetch_inventory(store: dict, snapshot: date) -> pd.DataFrame:
    rows = []
    for stock in paged(store, "item_stocks"):
        rows.append({
            "snapshot_date": snapshot.isoformat(),
            "location": store["name"],
            "product_id": (stock.get("item") or {}).get("id"),
            "quantity_on_hand": stock.get("stockCount") or stock.get("quantity") or 0,
            "days_in_stock": None,     # accumulates once you pull regularly
            "reorder_level": None,
        })
    return pd.DataFrame(rows)


def check(stores: list[dict]) -> None:
    for store in stores:
        info = get(store, "")  # /v3/merchants/{mId}
        print(f"OK  {store['name']}: token works — merchant '{info.get('name')}'")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=lambda s: date.fromisoformat(s),
                        default=date.today() - timedelta(days=365))
    parser.add_argument("--check", action="store_true",
                        help="only verify each store's token, no data pull")
    args = parser.parse_args()

    stores = load_env()
    if args.check:
        check(stores)
        return

    snapshot = date.today()
    out_dir = PRIVATE / snapshot.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    products, sales, inventory = [], [], []
    for store in stores:
        print(f"== {store['name']} ==")
        products.append(fetch_products(store))
        sales.append(fetch_sales(store, args.since))
        inventory.append(fetch_inventory(store, snapshot))

    # Same item can exist per-merchant; keep first occurrence per product_id.
    pd.concat(products).drop_duplicates("product_id").to_csv(out_dir / "products.csv", index=False)
    pd.concat(sales).to_csv(out_dir / "sales.csv", index=False)
    pd.concat(inventory).to_csv(out_dir / "inventory.csv", index=False)
    print(f"\nwritten to {out_dir} (git-ignored)")


if __name__ == "__main__":
    main()
