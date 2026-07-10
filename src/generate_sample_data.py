"""Generate synthetic (deliberately messy) POS data for a multi-location record store.

Produces three raw CSVs in data/raw/ modeled on point-of-sale exports:

    products_raw.csv   one row per catalog title
    sales_raw.csv      one row per line-item sale, 12 months
    inventory_raw.csv  monthly snapshot per location x product

The data is seeded and reproducible. Realistic mess is injected on purpose
(duplicates, missing values, inconsistent casing/dates, '$' prefixes, stray
whitespace) so the cleaning pipeline has real work to do.

Planted business patterns the analyses should surface:
  * Used LPs carry a higher margin % than new stock.
  * Jazz and Latin sell through strongly at Dania Beach.
  * Several titles are overstocked at Oakland Park while stocked out elsewhere.
  * Roughly a fifth of on-hand units have sat 90+ days.
  * December and April (Record Store Day) sales spikes.

Usage:
    python src/generate_sample_data.py [--seed 42]
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

LOCATIONS = ["Dania Beach", "Oakland Park", "Lake Worth"]
# Relative sales volume per store
LOCATION_WEIGHTS = {"Dania Beach": 0.45, "Oakland Park": 0.35, "Lake Worth": 0.20}

FORMATS = ["LP", "CD", "7\"", "Cassette"]
FORMAT_WEIGHTS = [0.62, 0.22, 0.10, 0.06]

GENRES = [
    "Rock", "Jazz", "Hip-Hop", "Latin", "Electronic",
    "Soul/Funk", "Metal", "Alternative", "Reggae", "Classical",
]
GENRE_WEIGHTS = [0.20, 0.14, 0.13, 0.12, 0.09, 0.09, 0.08, 0.08, 0.04, 0.03]

ARTISTS_BY_GENRE = {
    "Rock": ["Fleetwood Mac", "Led Zeppelin", "Pink Floyd", "The Rolling Stones", "Tom Petty", "Santana"],
    "Jazz": ["Miles Davis", "John Coltrane", "Herbie Hancock", "Alice Coltrane", "Thelonious Monk", "Grant Green"],
    "Hip-Hop": ["MF DOOM", "A Tribe Called Quest", "OutKast", "J Dilla", "Nas", "Wu-Tang Clan"],
    "Latin": ["Bad Bunny", "Buena Vista Social Club", "Celia Cruz", "Willie Colon", "Juan Luis Guerra", "Selena"],
    "Electronic": ["Aphex Twin", "Daft Punk", "Boards of Canada", "Burial", "Four Tet", "Floating Points"],
    "Soul/Funk": ["Marvin Gaye", "Curtis Mayfield", "Parliament", "Al Green", "Roy Ayers", "Sly & The Family Stone"],
    "Metal": ["Black Sabbath", "Metallica", "Iron Maiden", "Slayer", "Pantera", "Mastodon"],
    "Alternative": ["The Cure", "Radiohead", "Pixies", "Sonic Youth", "My Bloody Valentine", "Interpol"],
    "Reggae": ["Bob Marley", "Toots & The Maytals", "Burning Spear", "Augustus Pablo", "Gregory Isaacs", "Sister Nancy"],
    "Classical": ["Erik Satie", "Claude Debussy", "Philip Glass", "Arvo Part", "J.S. Bach", "Ryuichi Sakamoto"],
}

ALBUM_WORDS = [
    "Sessions", "Live at the Regal", "Vol. II", "Anthology", "Nights", "Motion",
    "Echoes", "Blueprint", "Horizons", "Reflections", "Standards", "Rarities",
    "In Dub", "Unplugged", "The Early Years", "Selected Works", "Interstellar",
    "Coastline", "Afterhours", "Basement Tapes", "Grooves", "Frequencies",
]

N_PRODUCTS = 300
SALES_START = date(2025, 7, 1)
SALES_END = date(2026, 6, 30)


def build_products(rng: random.Random) -> pd.DataFrame:
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        genre = rng.choices(GENRES, weights=GENRE_WEIGHTS)[0]
        artist = rng.choice(ARTISTS_BY_GENRE[genre])
        title = f"{rng.choice(ALBUM_WORDS)}"
        fmt = rng.choices(FORMATS, weights=FORMAT_WEIGHTS)[0]
        condition = rng.choices(["New", "Used"], weights=[0.55, 0.45])[0]
        release_year = rng.randint(1959, 2026)

        # Pricing logic: used stock is bought cheap and margins are strong;
        # new stock has distributor pricing with thinner margins.
        if condition == "Used":
            cost = round(rng.uniform(3.0, 14.0), 2)
            price = round(cost * rng.uniform(2.2, 3.4), 2)
        else:
            cost = round(rng.uniform(9.0, 26.0), 2)
            price = round(cost * rng.uniform(1.45, 1.85), 2)
        if fmt == "CD":
            cost, price = round(cost * 0.55, 2), round(price * 0.5, 2)
        elif fmt == "7\"":
            cost, price = round(cost * 0.35, 2), round(price * 0.4, 2)
        elif fmt == "Cassette":
            cost, price = round(cost * 0.4, 2), round(price * 0.45, 2)

        rows.append({
            "product_id": f"P{i:04d}",
            "sku": f"WGB-{rng.randint(10000, 99999)}",
            "artist": artist,
            "title": f"{artist.split(' ')[0]} {title}" if rng.random() < 0.15 else title,
            "format": fmt,
            "genre": genre,
            "condition": condition,
            "cost": cost,
            "price": price,
            "release_year": release_year,
        })
    return pd.DataFrame(rows)


def month_weight(d: date) -> float:
    """Seasonality: December gift rush and April Record Store Day spike."""
    if d.month == 12:
        return 1.8
    if d.month == 4:
        return 1.5
    if d.month in (1, 2):
        return 0.75
    return 1.0


def build_sales(rng: random.Random, products: pd.DataFrame) -> pd.DataFrame:
    # Popularity follows a heavy-tailed distribution: a few hits, a long tail.
    popularity = np.array([1 / (rank ** 0.7) for rank in range(1, len(products) + 1)])
    rng_np = np.random.default_rng(rng.randint(0, 2**31))
    rng_np.shuffle(popularity)

    # Planted pattern: Jazz and Latin over-index at Dania Beach.
    dania_boost = products["genre"].isin(["Jazz", "Latin"]).to_numpy() * 1.6 + 1.0

    rows = []
    sale_no = 1
    d = SALES_START
    while d <= SALES_END:
        base_transactions = 22 * month_weight(d)
        # Weekends are busier
        if d.weekday() >= 5:
            base_transactions *= 1.5
        n_lines = rng_np.poisson(base_transactions)
        for _ in range(n_lines):
            location = rng.choices(LOCATIONS, weights=list(LOCATION_WEIGHTS.values()))[0]
            w = popularity * (dania_boost if location == "Dania Beach" else 1.0)
            idx = rng_np.choice(len(products), p=w / w.sum())
            p = products.iloc[idx]
            quantity = rng.choices([1, 2, 3], weights=[0.88, 0.09, 0.03])[0]
            discount = rng.choices([0.0, 2.0, 5.0], weights=[0.86, 0.09, 0.05])[0]
            rows.append({
                "sale_id": f"S{sale_no:06d}",
                "sale_date": d.isoformat(),
                "location": location,
                "product_id": p["product_id"],
                "quantity": quantity,
                "unit_price": p["price"],
                "discount": discount,
            })
            sale_no += 1
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def build_inventory(rng: random.Random, products: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    """Monthly snapshots. Plants overstock/stockout pairs and aged stock."""
    sold_by_product = sales.groupby("product_id")["quantity"].sum()
    snapshot_dates = pd.date_range(SALES_START, SALES_END, freq="ME").date

    # Pick ~25 titles to be transfer candidates: piled up at Oakland Park,
    # stocked out at Dania Beach where demand exists.
    transfer_ids = set(
        products.sample(25, random_state=rng.randint(0, 2**31))["product_id"]
    )

    rows = []
    for snap in snapshot_dates:
        for _, p in products.iterrows():
            demand = int(sold_by_product.get(p["product_id"], 0))
            for location in LOCATIONS:
                # Baseline stock scaled loosely to demand
                qty = max(0, int(rng.gauss(mu=max(1, demand // 6), sigma=2)))
                days = rng.randint(5, 75)

                if p["product_id"] in transfer_ids:
                    if location == "Oakland Park":
                        qty = rng.randint(6, 14)          # overstocked
                        days = rng.randint(70, 200)       # and sitting
                    elif location == "Dania Beach":
                        qty = 0                            # stocked out
                        days = 0

                # ~20% of nonzero rows: aged stock 90+ days
                if qty > 0 and rng.random() < 0.20:
                    days = rng.randint(90, 320)

                rows.append({
                    "snapshot_date": snap.isoformat(),
                    "location": location,
                    "product_id": p["product_id"],
                    "quantity_on_hand": qty,
                    "days_in_stock": days,
                    "reorder_level": rng.choice([1, 2, 2, 3]),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mess injection — raw files should look like real exports, not clean tables.
# ---------------------------------------------------------------------------

def messy_dates(series: pd.Series, rng: random.Random, frac: float = 0.12) -> pd.Series:
    """Rewrite a fraction of ISO dates as M/D/YYYY, as mixed exports often do."""
    def maybe_us(iso: str) -> str:
        if rng.random() < frac:
            y, m, d = iso.split("-")
            return f"{int(m)}/{int(d)}/{y}"
        return iso
    return series.map(maybe_us)


def messy_case(series: pd.Series, rng: random.Random, frac: float = 0.08) -> pd.Series:
    def maybe_case(v: str) -> str:
        r = rng.random()
        if r < frac / 2:
            return v.upper()
        if r < frac:
            return v.lower()
        return v
    return series.map(maybe_case)


def messy_money(series: pd.Series, rng: random.Random, frac: float = 0.06) -> pd.Series:
    """Prefix some prices with '$' — a classic spreadsheet-export artifact."""
    return series.map(lambda v: f"${v}" if rng.random() < frac else v)


def messy_whitespace(series: pd.Series, rng: random.Random, frac: float = 0.05) -> pd.Series:
    return series.map(lambda v: f"  {v} " if rng.random() < frac else v)


def inject_nulls(df: pd.DataFrame, column: str, rng: random.Random, frac: float) -> None:
    mask = [rng.random() < frac for _ in range(len(df))]
    df.loc[mask, column] = None


def duplicate_rows(df: pd.DataFrame, rng: random.Random, frac: float = 0.012) -> pd.DataFrame:
    dupes = df.sample(frac=frac, random_state=rng.randint(0, 2**31))
    out = pd.concat([df, dupes], ignore_index=True)
    return out.sample(frac=1.0, random_state=rng.randint(0, 2**31)).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    products = build_products(rng)
    sales = build_sales(rng, products)
    inventory = build_inventory(rng, products, sales)

    # --- make it messy ---
    products_raw = products.copy()
    products_raw["genre"] = messy_case(products_raw["genre"], rng)
    products_raw["artist"] = messy_whitespace(products_raw["artist"], rng)
    products_raw["price"] = messy_money(products_raw["price"].astype(str), rng)
    inject_nulls(products_raw, "release_year", rng, 0.04)
    inject_nulls(products_raw, "sku", rng, 0.03)
    products_raw = duplicate_rows(products_raw, rng)

    sales_raw = sales.copy()
    sales_raw["sale_date"] = messy_dates(sales_raw["sale_date"], rng)
    sales_raw["location"] = messy_case(sales_raw["location"], rng)
    sales_raw["unit_price"] = messy_money(sales_raw["unit_price"].astype(str), rng)
    inject_nulls(sales_raw, "discount", rng, 0.05)
    sales_raw = duplicate_rows(sales_raw, rng)

    inventory_raw = inventory.copy()
    inventory_raw["location"] = messy_case(inventory_raw["location"], rng)
    inject_nulls(inventory_raw, "reorder_level", rng, 0.03)
    inventory_raw = duplicate_rows(inventory_raw, rng, frac=0.008)

    products_raw.to_csv(RAW_DIR / "products_raw.csv", index=False)
    sales_raw.to_csv(RAW_DIR / "sales_raw.csv", index=False)
    inventory_raw.to_csv(RAW_DIR / "inventory_raw.csv", index=False)

    print(f"seed={args.seed}")
    print(f"products_raw.csv   {len(products_raw):>7,} rows")
    print(f"sales_raw.csv      {len(sales_raw):>7,} rows")
    print(f"inventory_raw.csv  {len(inventory_raw):>7,} rows")
    print(f"written to {RAW_DIR}")


if __name__ == "__main__":
    main()
