# Executive Summary

Twelve months of point-of-sale data (July 2025 – June 2026) across three
store locations: **$242,343 revenue on 11,294 units sold**, blended gross
margin **45.6%**. Five findings, each actionable.

## 1. Used inventory is the margin engine

Used stock earned a **61.8% gross margin vs. 39.0% for new** — consistent
across every format (used 7" singles peak at 68.5%). Used product generated
29% of revenue but 39% of gross profit. **Recommendation:** grow the buy
counter; every dollar spent buying used collections outperforms a dollar of
distributor orders.

## 2. Store demand is local — stock accordingly

Dania Beach leads revenue ($108k of $242k) and its mix is distinct: **Jazz
and Latin alone account for 54% of its revenue**, roughly double their
share at the other stores. Lake Worth's sell-through (58.0%) trails Dania
Beach (76.4%) — its shelves hold proportionally more stock than its sales
support. **Recommendation:** allocate new arrivals by store-level genre
demand, not evenly.

## 3. ~$3,300 of 90-day revenue is sitting in the wrong building

The transfer analysis found **56 unique titles overstocked at one store
while stocked out at another that demonstrated demand** — an estimated
**$3,266 of 90-day revenue** recoverable by moving stock between stores
instead of purchasing. Top example: Buena Vista Social Club LPs sitting
120 days at Oakland Park while Dania Beach sold 14 units in 90 days.

## 4. One unit in five is shelf furniture

**19.1% of on-hand units have been in stock 90+ days**, and 106
location-title piles hold 6+ units that haven't moved in 60+ days.
**Recommendation:** a quarterly markdown/promo cycle for the 90+ bucket,
prioritized by cost tied up.

## 5. Stockouts are quietly taxing the best sellers

**164 product-location combinations were out of stock at the latest
snapshot despite recent demand** — including titles selling 8–15 units per
60 days elsewhere. Between transfers (#3) and reorder-level review, most
of these are avoidable without new spend.

---

*Method: synthetic POS data modeled on Clover export formats → Python
cleaning pipeline (every correction logged in
[data_quality_report.md](data_quality_report.md)) → SQLite → SQL analyses
(`sql/`, results in [analysis/](analysis/)) → Streamlit dashboard.*
