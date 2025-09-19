# 🛒 Mancino Market  
## Synthetic Grocery Retail Dataset (Public, Data-Only)

**Mancino Market** is a fully synthetic grocery retail dataset set in Manhattan, NYC. It’s designed for teaching, analytics, and modeling—rich enough to feel real, safe enough to share.

> 🔒 This repository is **data-only**: CSVs and docs that anyone can download and analyze. All generation/validation code lives in a **private tools repo** and is intentionally not included here.

---

## 🚀 What’s in v1.5 (2025-09-21)

**New**
- **Weekly promotions** (Sunday-start weeks) with four mechanics:
  - `BOGO`, `BUNDLE`, `COUPON`, `MANAGER_SPECIAL`
- **Promotion audit log** → `transaction_promotions.csv`
- **Inventory events** (stockouts & nightly replenishment) → `inventory_events.csv`
- **Transactions extended** through **2025-09-21** (previously through 2025-08-24)

**Promotion behavior**
- Scope by **SKU** or **Category**
- Store targeting via `store_scope` = `ALL` or comma-separated store IDs
- `priority` (higher wins) and `can_stack` (stacking rules)
- Weeks are **Sunday → Saturday** (e.g., `week_start=2025-09-14` covers Sep 14–20, 2025)

---

## 🌆 About Mancino

**MANCINO** = **M**idtown **A**rea to **N**oHo, **C**helsea, **I**nter-village, and **N**olita.

Five fictional stores:
1. Midtown  
2. NoHo  
3. Chelsea  
4. Greenwich Village  
5. Nolita

---

## 📁 Repository Layout

data/
v1_2025-09-21/
customers.csv
products.csv
product_store_inventory.csv
promotions.csv
stores.csv
transactions.csv
transaction_line_items.csv
transaction_promotions.csv
inventory_events.csv
notebooks/
(example notebooks only; no Python scripts in public repo)
README.md

> ⚠️ Policy: this public repo intentionally contains **no `.py` scripts**. Please don’t open PRs that add them.

---

## 📊 File Guide (per version folder)

| File | Description | Notes |
|---|---|---|
| `stores.csv` | Store master | IDs, names, neighborhoods, optional geos |
| `products.csv` | Product catalog | Brand, size, category, price/tax |
| `product_store_inventory.csv` | Store×SKU on-hand | Starting stock for simulation; used to model stockouts |
| `customers.csv` | Customers | Synthetic NYC locations & home-store affinity |
| `promotions.csv` | **Weekly promotions** | Types: BOGO, BUNDLE, COUPON, MANAGER_SPECIAL; scope, stacking, priority |
| `transactions.csv` | Transaction headers | Coverage includes **through 2025-09-21** |
| `transaction_line_items.csv` | Line items | Final line totals reflect applied promos |
| `transaction_promotions.csv` | **Promo audit** | One row per applied promotion→line |
| `inventory_events.csv` | **Inventory log** | `STOCKOUT` and `REPLENISHMENT` events |

---

## 🧾 Promotions Schema (v1.5)

**Core columns**
- `promotion_id` (string)
- `promo_type` ∈ {`BOGO`,`BUNDLE`,`COUPON`,`MANAGER_SPECIAL`}
- `name` (string)
- `week_start`, `week_end` (YYYY-MM-DD; `week_start` is a **Sunday**)
- `scope_type` ∈ {`sku`,`category`}, `scope_id` (string)
- `store_scope` ∈ {`ALL` or comma-separated store IDs}

**Value columns** (type-dependent)
- `amount_off`, `percent_off`, `new_price`
- `buy_qty`, `get_qty`
- `bundle_qty`, `bundle_price`
- `min_qty`, `min_spend`

**Control columns**
- `priority` (int; higher takes precedence)
- `can_stack` (bool)
- `limit_per_customer`, `notes`, `active` (bool)

**Applied promotions log** → `transaction_promotions.csv`
transaction_id, line_item_id, promotion_id, qty_discounted, discount_amount, applied_price, rule_note

---

## 🧪 What you can do with this dataset

- Measure **promo lift** by store/category/segment
- Analyze **stockout** impact on sales & **fill rate**
- Study **basket composition** and **size** changes during promos
- Build **forecasting** and **uplift models** for promotions
- Teach joins, time windows, and event modeling with real-ish data

---

## 🔎 Quick Start (Python / pandas)

```python
import pandas as pd

V = "v1_2025-09-21"
root = f"./data/{V}"

tx = pd.read_csv(f"{root}/transactions.csv", parse_dates=["txn_ts"])
li = pd.read_csv(f"{root}/transaction_line_items.csv")
tp = pd.read_csv(f"{root}/transaction_promotions.csv")
pr = pd.read_csv(f"{root}/promotions.csv", parse_dates=["week_start","week_end"])

# Example: weekly promo penetration (share of transactions with any promo)
has_promo_tx = set(tp["transaction_id"].unique())
weekly_pen = (tx.assign(has_promo=tx["transaction_id"].isin(has_promo_tx))
                .set_index("txn_ts")
                .resample("W-SUN")["has_promo"]
                .mean())
print(weekly_pen.tail())
🤝 Contributing
Issues and discussions welcome.
Note: Pull requests that add .py files will not be accepted here (this is a data-only repository). Improvements to data and documentation are welcome.
📚 License
Creative Commons CC BY 4.0 — share and adapt with attribution.
Full text: https://creativecommons.org/licenses/by/4.0/legalcode
Maintainer: Dr. Jose Mendoza — https://www.jose-mendoza.com
Last update: 2025-09-21