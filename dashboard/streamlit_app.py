"""Retail Inventory & Sales Analytics dashboard.

Four views over the analysis database: Overview, Products, Inventory
Health, and Transfers. Reads the same named SQL queries the CLI runner
uses (sql/*.sql, tagged with `-- :name`), so dashboard and exported
reports can never drift apart.

Run:
    streamlit run dashboard/streamlit_app.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from run_analysis import ANALYSIS_FILES, named_queries  # noqa: E402

DB_PATH = ROOT / "data" / "processed" / "store.db"

# The .db is git-ignored; on a fresh checkout (e.g. Streamlit Cloud) build
# it from the committed cleaned CSVs.
if not DB_PATH.exists():
    import load_db
    load_db.main()

# --- palette (fixed identity colors; magnitude bars use a single hue) ---
BLUE, AQUA, YELLOW = "#2a78d6", "#1baf7a", "#eda100"
LOCATION_COLORS = {"Dania Beach": BLUE, "Oakland Park": AQUA, "Lake Worth": YELLOW}
ORDINAL_BLUES = ["#86b6ef", "#5598e7", "#2a78d6", "#184f95"]  # light -> dark
INK_MUTED = "#898781"
GRID = "#e1e0d9"

st.set_page_config(
    page_title="Retail Inventory & Sales Analytics",
    page_icon="📦",
    layout="wide",
)


@st.cache_data
def load_queries() -> dict[str, pd.DataFrame]:
    con = sqlite3.connect(DB_PATH)
    try:
        results: dict[str, pd.DataFrame] = {}
        for sql_file in ANALYSIS_FILES:
            text = (ROOT / "sql" / sql_file).read_text(encoding="utf-8")
            for name, query in named_queries(text).items():
                results[name] = pd.read_sql_query(query, con)
        return results
    finally:
        con.close()


def style_fig(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Segoe UI', system-ui, sans-serif", color="#52514e"),
        showlegend=False,
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color=INK_MUTED)),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color=INK_MUTED)),
    )
    return fig


data = load_queries()

st.title("Retail Inventory & Sales Analytics")
st.caption(
    "Fictional multi-location record store · 12 months of POS data · "
    "synthetic dataset modeled on Clover export formats"
)

tab_overview, tab_products, tab_inventory, tab_transfers = st.tabs(
    ["Overview", "Products", "Inventory health", "Transfers"]
)

# ---------------------------------------------------------------- Overview
with tab_overview:
    monthly = data["monthly_revenue"]
    by_loc = data["revenue_by_location"]
    margin = data["margin_by_condition"]
    stockouts = data["stockouts"]
    transfers = data["transfer_recommendations"]

    total_rev = monthly["revenue"].sum()
    total_units = int(monthly["units"].sum())
    blended_margin = 100 * margin["gross_profit"].sum() / margin["revenue"].sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Revenue (12 mo)", f"${total_rev / 1000:,.0f}k")
    k2.metric("Units sold", f"{total_units:,}")
    k3.metric("Gross margin", f"{blended_margin:.1f}%")
    k4.metric("Stockouts", len(stockouts), help="Products with zero on hand and demonstrated 60-day demand")
    k5.metric("Transfer opps", len(transfers), help="Overstock at one store, stockout at another")

    c1, c2 = st.columns((3, 2))
    with c1:
        st.subheader("Monthly revenue")
        fig = px.line(monthly, x="month", y="revenue", markers=True)
        fig.update_traces(line_color=BLUE, line_width=2, marker=dict(size=8, color=BLUE))
        fig.update_yaxes(tickprefix="$", rangemode="tozero")
        st.plotly_chart(style_fig(fig), width="stretch")
        st.caption("December gift rush and April Record Store Day drive the two peaks.")
    with c2:
        st.subheader("Revenue by store")
        fig = px.bar(
            by_loc, x="location", y="revenue",
            color="location", color_discrete_map=LOCATION_COLORS,
            text_auto=".2s",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(tickprefix="$")
        st.plotly_chart(style_fig(fig), width="stretch")

    st.subheader("Genre mix by store")
    genre_loc = data["genre_by_location"]
    fig = px.bar(
        genre_loc, x="genre", y="revenue",
        facet_col="location", color="location",
        color_discrete_map=LOCATION_COLORS,
        category_orders={"location": list(LOCATION_COLORS)},
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_yaxes(tickprefix="$")
    st.plotly_chart(style_fig(fig, height=300), width="stretch")
    st.caption("Jazz and Latin over-index at Dania Beach — stock decisions should be store-specific.")

# ---------------------------------------------------------------- Products
with tab_products:
    c1, c2 = st.columns((3, 2))
    with c1:
        st.subheader("Top 15 titles by revenue")
        top = data["top_products"].copy()
        top["revenue"] = top["revenue"].map("${:,.2f}".format)
        st.dataframe(top, width="stretch", hide_index=True)
    with c2:
        st.subheader("Revenue by genre")
        genre = data["revenue_by_genre"].sort_values("revenue")
        fig = px.bar(genre, x="revenue", y="genre", orientation="h", text_auto=".2s")
        fig.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False)
        fig.update_xaxes(tickprefix="$")
        st.plotly_chart(style_fig(fig, height=420), width="stretch")

    st.subheader("Margin: used vs. new")
    mfc = data["margin_by_format_condition"]
    fig = px.bar(
        mfc, x="format", y="margin_pct", color="condition",
        barmode="group",
        color_discrete_map={"Used": BLUE, "New": AQUA},
        text_auto=".1f",
        category_orders={"format": ["LP", "CD", "7\"", "Cassette"]},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(title="gross margin %")
    fig.update_layout(showlegend=True)
    st.plotly_chart(style_fig(fig, height=320), width="stretch")
    st.caption(
        "Used stock margins roughly 62% vs 39% for new across every format — "
        "the buy counter is the most profitable desk in the company."
    )

    st.subheader("Dead stock (no sales in 90 days)")
    st.dataframe(data["dead_stock"], width="stretch", hide_index=True)

# ---------------------------------------------------------------- Inventory
with tab_inventory:
    c1, c2 = st.columns((2, 3))
    with c1:
        st.subheader("Shelf age of on-hand units")
        aging = data["aging_buckets"].copy()
        aging["age_bucket"] = aging["age_bucket"].str[3:]  # strip sort prefix
        fig = px.bar(
            aging, x="age_bucket", y="units",
            color="age_bucket",
            color_discrete_sequence=ORDINAL_BLUES,
            text="pct_of_units",
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False)
        st.plotly_chart(style_fig(fig, height=340), width="stretch")
        st.caption("About one unit in five has been on the shelf 90+ days.")
    with c2:
        st.subheader("Sell-through by store")
        stl = data["sell_through_by_location"]
        fig = px.bar(
            stl, x="location", y="sell_through_pct",
            color="location", color_discrete_map=LOCATION_COLORS,
            text_auto=".1f",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(title="sell-through %", range=[0, 100])
        st.plotly_chart(style_fig(fig, height=340), width="stretch")

    st.subheader("Overstock — 6+ on hand, sitting 60+ days")
    st.dataframe(data["overstock"], width="stretch", hide_index=True)

    st.subheader("Stockouts with recent demand")
    st.dataframe(data["stockouts"], width="stretch", hide_index=True)

# ---------------------------------------------------------------- Transfers
with tab_transfers:
    st.subheader("Store-to-store transfer recommendations")
    st.markdown(
        "Titles **overstocked at one store and out of stock at another** with "
        "demonstrated demand. Moving them costs a car trip, not a purchase "
        "order. Ranked by estimated 90-day revenue at the destination."
    )
    tr = data["transfer_recommendations"]

    # One product transferable from two stores is one opportunity — dedupe
    # by destination+title for the chart (the full table keeps all sources).
    top10 = tr.drop_duplicates(subset=["to_location", "artist", "title"]).head(10).copy()
    top10["label"] = top10["artist"] + " — " + top10["title"]
    fig = px.bar(
        top10.sort_values("est_90d_revenue_at_dest"),
        x="est_90d_revenue_at_dest", y="label", orientation="h",
        text_auto=".2s",
    )
    fig.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="est. 90-day revenue at destination", tickprefix="$")
    fig.update_yaxes(title="")
    st.plotly_chart(style_fig(fig, height=380), width="stretch")

    st.dataframe(tr, width="stretch", hide_index=True)

    est_total = tr.drop_duplicates(subset=["to_location", "artist", "title"])["est_90d_revenue_at_dest"].sum()
    st.caption(
        f"Acting on unique recommendations represents roughly "
        f"**${est_total:,.0f}** of estimated 90-day revenue recovered "
        f"without buying new inventory."
    )
