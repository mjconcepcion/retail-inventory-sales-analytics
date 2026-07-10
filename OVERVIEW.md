# Retail Inventory & Sales Analytics — Project Overview

**Repo name:** `retail-inventory-sales-analytics`
**One-liner:** End-to-end analytics for a fictional multi-location record store — Python ETL, SQL analysis, and a dashboard that answers a real operations question.

---

## Why this project

This is the flagship public project for Misael's Data Analyst / BI Analyst job search. It's chosen because it:

- Maps 1:1 to the resume story: **SQL + Python ETL + data validation + dashboards** (the Wilen Group skill set, demonstrated in public).
- Uses a domain Misael actually knows (record store inventory), which makes interview conversation natural and the project memorable.
- Answers a business question a recruiter understands in 30 seconds:

> **"Which products are selling, which are sitting too long, and what inventory should be transferred between locations?"**

The goal is a clean, complete, recruiter-friendly repo — **not** a complex app. A recruiter should be able to skim the README, see screenshots and findings, and think "this person can clean data, write SQL, build dashboards, and explain business problems."

## Deliverables (definition of done)

- [ ] Synthetic raw datasets (deliberately messy) + the Python script that generates them
- [ ] Python cleaning/ETL pipeline with before/after data-quality metrics
- [ ] SQLite database + schema (`create_tables.sql`)
- [ ] 6 SQL analyses (below), each in its own commented `.sql` file
- [ ] Streamlit dashboard with the key views
- [ ] `reports/executive_summary.md` — findings written in plain business language
- [ ] README: problem → data → tools → process → findings → screenshots → how to run
- [ ] Repo pushed to github.com/mjconcepcion with a clean, intentional commit history
- [ ] Project card added to the portfolio site (misael's landing page) with repo link

## Data strategy: Clover-shaped synthetic data

The company runs **3 stores as separate Clover merchant accounts**. Misael has admin privileges on two (can create read-only API tokens) and manager access on the third (CSV report exports). The stores' real data is confidential and stays off GitHub, but we use the access in safe ways:

1. **Schema realism** — the synthetic generator emits CSVs matching **Clover's actual export formats** (Item Sales, Sales Report, Inventory export). The README can truthfully say the pipeline ingests Clover POS export formats — a real-world credential, not a toy format.
2. **Private validation** — real data runs through the same pipeline locally (git-ignored `data/private/`), so findings and interview talking points are grounded in real behavior. Nothing confidential is ever committed.
3. **API ingestion module (later phase)** — `src/fetch_clover.py` pulls orders/items/stock from the two admin stores via the Clover REST API (read-only tokens in git-ignored `.env`) and normalizes into the pipeline's canonical schema; the manager-access store ingests via CSV export. The script itself is public — heterogeneous multi-store ingestion is a strong real-world credential.

Optional v2 (owner permission required): publish anonymized, rescaled real data — or deliver the transfer-recommendation analysis to the owner as a real business win.

## Data model

Three CSVs, generated synthetically with realistic mess (typos, duplicate rows, missing values, inconsistent casing/dates — so the cleaning step has something real to do), with columns aligned to Clover export equivalents where they exist:

| File | Grain | Key fields |
|---|---|---|
| `products.csv` | one row per title | product_id, artist, title, format (LP/CD/7"), genre, condition (new/used), cost, price, release_year |
| `sales.csv` | one row per line-item sale | sale_id, sale_date, location, product_id, quantity, unit_price, discount |
| `inventory.csv` | monthly snapshot per location×product | snapshot_date, location, product_id, quantity_on_hand, days_in_stock, reorder_level |

Store locations: 3 fictional South Florida shops (e.g., Dania, Oakland Park, Lake Worth). ~300 products, ~12 months of sales (~5–8k rows), monthly inventory snapshots.

## The six SQL analyses

1. **Revenue & units** — by location, genre, format, month (trend)
2. **Top / bottom products** — best sellers and dead stock by units and revenue
3. **Inventory health** — overstock (qty > threshold and days_in_stock > 60), stockouts, aging buckets
4. **Transfer recommendations** ⭐ — products overstocked at one location and out of stock at another; the "money" query that shows business value
5. **Gross margin** — by genre, format, new vs. used (is used vinyl the margin winner?)
6. **Sell-through rate** — units sold vs. on-hand by genre/location, flags slow-moving categories

## Dashboard (Streamlit)

Four views, kept simple:
1. **Overview** — KPIs (revenue, units, margin %, stockout count) + monthly revenue trend
2. **Products** — top sellers, dead stock table with filters
3. **Inventory health** — aging chart, overstock/stockout tables by location
4. **Transfers** — the recommendation table: from-store, to-store, product, quantities

Hosted on Streamlit Community Cloud (free, public URL) with screenshots in the repo for recruiters who won't run anything.

## Tech stack

- **Python 3.12** — pandas for generation + cleaning
- **SQLite** — zero-install, file-based; schema and queries are standard SQL (portable to Postgres, which is on the resume)
- **Streamlit + Plotly** — dashboard
- **Git/GitHub** — clean incremental commits, one logical step each

## Phases

**Phase 0 — Environment & repo skeleton**
Install Python (none currently on this machine — winget), create venv, git init, folder structure, README stub, .gitignore, requirements.txt. First commit.

**Phase 1 — Data generation + cleaning**
First: Misael exports sample Item Sales / Sales Report / Inventory CSVs from the Clover dashboard (small date range is fine) so the generator can mirror the real schema. Then `src/generate_sample_data.py` (messy raw CSVs in Clover-shaped format, seeded/reproducible) and `src/clean_data.py` (validation, dedupe, standardization → processed CSVs + a data-quality report: rows in/out, duplicates removed, nulls fixed). `data/private/` is git-ignored for real exports. Commits: generator, then cleaner.

**Phase 2 — Database + SQL analysis**
`src/load_db.py` loads processed CSVs into SQLite. Write the six analysis queries in `sql/`, plus `run_analysis.py` that executes them and dumps result tables to `reports/`. Commit per analysis group.

**Phase 3 — Dashboard**
`dashboard/streamlit_app.py` with the four views. Screenshots into `reports/dashboard_screenshots/`. Deploy to Streamlit Cloud.

**Phase 4 — Polish & publish**
Executive summary with 5 concrete findings (real numbers from the data). Full README with screenshots. Push to GitHub, pin the repo, add the project card + link to the portfolio landing page (replacing one "repo soon" placeholder with a real link).

## Non-goals (v1)

No machine learning, no React/custom frontend, no Docker, no cloud infra, no auth, no external APIs (Discogs/Clover), no real scraped data. Any of these can be a v2 talking point; v1 optimizes for **finished and legible**.

## Repo structure

```
retail-inventory-sales-analytics/
├── README.md
├── OVERVIEW.md            (this file)
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/               (generated messy CSVs)
│   └── processed/         (cleaned CSVs; .db ignored)
├── src/
│   ├── generate_sample_data.py
│   ├── clean_data.py
│   ├── load_db.py
│   └── run_analysis.py
├── sql/
│   ├── create_tables.sql
│   ├── sales_analysis.sql
│   ├── inventory_health.sql
│   ├── transfer_recommendations.sql
│   ├── margin_analysis.sql
│   └── sell_through.sql
├── reports/
│   ├── executive_summary.md
│   ├── data_quality_report.md
│   └── dashboard_screenshots/
└── dashboard/
    └── streamlit_app.py
```

## How this feeds the job search

- **Resume bullet:** "Built an end-to-end retail analytics project using Python, SQL, and Streamlit to clean sales/inventory data, analyze revenue and margin trends, identify slow-moving stock, and generate store-to-store transfer recommendations."
- **Portfolio site:** becomes a featured project with a live dashboard link — the first "repo soon" placeholder to be replaced with a real repo.
- **Recruiter pitch:** concrete proof behind "SQL, Python, ETL, data quality, dashboards."
