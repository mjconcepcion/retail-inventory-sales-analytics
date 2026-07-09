# Retail Inventory & Sales Analytics

End-to-end analytics for a fictional multi-location record store: Python ETL, SQL analysis, and an interactive dashboard that answer one operations question —

> **Which products are selling, which are sitting too long, and what inventory should be transferred between locations?**

The pipeline ingests point-of-sale data modeled on Clover POS export formats, cleans and validates it, loads it into SQLite, and surfaces findings through SQL analyses and a Streamlit dashboard.

> 🚧 **Work in progress.** Build plan and scope live in [OVERVIEW.md](OVERVIEW.md).

## Planned stack

- **Python / pandas** — synthetic data generation and cleaning pipeline with data-quality reporting
- **SQLite** — schema + six analysis queries (revenue, product performance, inventory health, transfer recommendations, margin, sell-through)
- **Streamlit + Plotly** — interactive dashboard

## Project structure

```
├── data/
│   ├── raw/          # generated messy CSVs (Clover-shaped)
│   ├── processed/    # cleaned output
│   └── private/      # local-only real exports (git-ignored)
├── src/              # generation, cleaning, load, analysis scripts
├── sql/              # schema + analysis queries
├── reports/          # executive summary, data-quality report, screenshots
└── dashboard/        # Streamlit app
```

---

*Misael Concepcion · [github.com/mjconcepcion](https://github.com/mjconcepcion) · misael.j.concepcion@gmail.com*
