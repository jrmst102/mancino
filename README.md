# 🛒 Mancino Market
## Synthetic Grocery Retail Dataset (Public, Data-Only)

Mancino Market is a fully synthetic grocery retail dataset set in Manhattan, NYC. It’s designed for teaching, analytics, and modeling—rich enough to feel real, safe enough to share.

---

## What’s new in v1.6 (2025-11-01)

New
- Inventory event stream → `inventory_events.csv` (stockouts, adjustments, etc.)
- Promotions schema simplified (uses `start_date`/`end_date`, `mechanic`, `get_type`; store targeting via `promotion_stores.csv` only)
- Transactions and line items schemas streamlined (see Schemas section)

Changed
- Transaction currency fields now use decimal dollars (`subtotal`, `tax`, `total`) vs cents in prior version
- `transactions.csv` now includes `num_items`, `payment_type`, `day_name`; `store_id` is numeric (1..5)
- `transaction_line_items.csv` columns reduced to essentials and uses `line_no`
- `transaction_promotions.csv` columns updated to `transaction_id,line_no,promotion_id,mechanic,savings`

Removed (from core v1.6 folder)
- `daily_prices.csv` (still available in v1_2025-09-21; regenerate via `notebooks/get_daily_prices.py` if needed)
- Derived samples `mancino_daily_sales.csv`, `weekend_visit_dataset.csv` (kept in v1_2025-09-21)

Compatibility notes
- Store IDs continue to appear as numeric (e.g., `1..5` in `stores.csv`, `transactions.csv`, `promotion_stores.csv`) and string-coded (`S0001` in `product_store_inventory.csv`, `customers.csv`). See “Joining tips”.

---

## What’s in v1.5 (2025-09-21)

New
- Weekly promotions (Sunday-start weeks) with four mechanics: BOGO, BUNDLE, COUPON, MANAGER_SPECIAL
- Promotion audit log → `transaction_promotions.csv`
- Daily price history → `daily_prices.csv`
- Transactions extended through 2025-09-21 (previously through 2025-08-24)

Promotion behavior
- Scope by SKU or Category
- Store targeting via `store_scope` (ALL or IDs) and normalized link tables
- Priority (higher wins) and can_stack (stacking rules)
- Weeks are Sunday → Saturday (e.g., `week_start=2025-09-14` covers Sep 14–20, 2025)

Data notes
- Store IDs appear in two formats across files: `S0001`-style strings and numeric `1..5`. See “Joining tips” below.

---

## About Mancino

MANCINO = Midtown Area to NoHo, Chelsea, Inter‑village, and Nolita.

Five fictional stores:
1. Midtown
2. NoHo
3. Chelsea
4. Greenwich Village
5. Nolita

---

## 📁 Repository layout

data/
├── v1_2025-08-24/                # Initial public drop (no promotions or daily prices)
│   ├── customers.csv
│   ├── product_store_inventory.csv
│   ├── products.csv
│   ├── promotions.csv
│   ├── stores.csv
│   ├── transaction_line_items.csv
│   └── transactions.csv
├── v1_2025-09-21/                # v1.5 — adds promotions, price history, and derived samples
│   ├── customers.csv
│   ├── daily_prices.csv
│   ├── mancino_daily_sales.csv
│   ├── product_store_inventory.csv
│   ├── products.csv
│   ├── promo_class_dataset.csv
│   ├── promotion_items.csv
│   ├── promotion_stores.csv
│   ├── promotions.csv
│   ├── stores.csv
│   ├── transaction_line_items.csv
│   ├── transaction_promotions.csv
│   └── transactions.csv
└── v1_2025-11-01/                # v1.6 — inventory events, updated schemas
  ├── customers.csv
  ├── inventory_events.csv
  ├── product_store_inventory.csv
  ├── products.csv
  ├── promo_class_dataset.csv
  ├── promotion_items.csv
  ├── promotion_stores.csv
  ├── promotions.csv
  ├── stores.csv
  ├── transaction_line_items.csv
  ├── transaction_promotions.csv
  └── transactions.csv

notebooks/
└── Example notebooks and helper scripts

README.md

---

## 📊 File guide (per version folder)

| File | Description | Notes |
|---|---|---|
| `stores.csv` | Store master | ID, name, neighborhood, address, city, state, zip, lat/lon |
| `products.csv` | Product catalog | Brand, size, category/subcategory, unit list price, unit cost |
| `product_store_inventory.csv` | Store×SKU on-hand | On-hand units, reorder point, optional base price override (cents), active flag |
| `customers.csv` | Customers | Synthetic NYC customers with home-store affinity |
| `promotions.csv` | Promotions (header) | v1.6 uses `start_date`/`end_date`, `mechanic`, `get_type`, `priority`; no `store_scope` column |
| `promotion_items.csv` | Promotion↔SKU links | Narrow a promotion to specific SKUs when `scope_type=sku` |
| `promotion_stores.csv` | Promotion↔Store links | Narrow a promotion to specific stores (numeric `store_id` 1..5) |
| `transactions.csv` | Transaction headers | v1.6 fields are decimal-dollar `subtotal/tax/total`, plus `num_items`, `payment_type`, `day_name` |
| `transaction_line_items.csv` | Line items | v1.6 columns reduced to `transaction_id,line_no,product_id,qty,unit_price,line_subtotal,line_discount,line_total` |
| `transaction_promotions.csv` | Promotion audit | v1.6 columns `transaction_id,line_no,promotion_id,mechanic,savings` |
| `inventory_events.csv` | Inventory event log | v1.6 only. Columns: `event_ts,store_id,product_id,delta,reason` |
| `daily_prices.csv` | Daily price history | v1.5 only. Baseline price by store and SKU on a date |

---

## 📐 Schemas (key columns)

These reflect the public CSVs; where schemas changed, both versions are noted.

### stores.csv
- store_id, store_name, neighborhood, address, city, state, zip, latitude, longitude
  - Note: `store_id` is numeric here (e.g., 1..5).

### products.csv
- product_id, product_name, brand, category, subcategory, unit_size, price, unit_cost

### product_store_inventory.csv
- product_id, store_id, on_hand_units, reorder_point, base_price_override_cents, active
  - `store_id` uses `S0001` format here. `base_price_override_cents` is optional.

### customers.csv
- See file for columns (synthetic customer master).

### promotions.csv
- v1.5 (2025-09-21): week-based header with `week_start/week_end`, stacking rules, scope and optional `store_scope`
- v1.6 (2025-11-01): start/end dates with simplified fields
  - bundle_qty, buy_qty, can_stack, category, end_date, get_qty, get_type, mechanic, name, percent_off, priority, promotion_id, scope_type, start_date
  - Store targeting via `promotion_stores.csv` (no `store_scope` column)

### promotion_items.csv
- v1.5: promotion_id, sku_id
- v1.6: promotion_id, product_id

### promotion_stores.csv
- promotion_id, store_id (numeric 1..5)

### transactions.csv
- v1.5: transaction_id, store_id, customer_id, txn_ts, channel, subtotal_cents, tax_cents, total_cents, __tid_num, net_sales (store_id like `S0001`)
- v1.6: transaction_id, customer_id, store_id, txn_ts, subtotal, tax, total, num_items, payment_type, day_name (store_id numeric 1..5)

### transaction_promotions.csv
- v1.5: transaction_id, line_item_id, promotion_id, qty_discounted, discount_amount, applied_price, rule_note
- v1.6: transaction_id, line_no, promotion_id, mechanic, savings

### transaction_line_items.csv
- v1.5: transaction_id, line_number, product_id, category, unit_cost, unit_price, promo_price, qty, line_subtotal, line_discount, line_total, promo_id, promo_type, plus helper columns
- v1.6: transaction_id, line_no, product_id, qty, unit_price, line_subtotal, line_discount, line_total

### inventory_events.csv (v1.6 only)
- event_ts, store_id (numeric), product_id, delta, reason

### daily_prices.csv (v1.5 only)
- store_id (numeric), sku_id, date, price

---

## 🔗 Joining tips (IDs and formats)

- Store IDs appear as both numeric (e.g., `1..5` in `stores.csv`, `transactions.csv`, `promotion_stores.csv`) and string-coded (e.g., `S0001` in `product_store_inventory.csv`, `customers.csv`).
  - To join across versions/files: either pad numeric IDs to `S000x` (e.g., 3 → S0003) or strip the `S` prefix and left zeros to get an integer.
- Product/SKU IDs use `Pxxxxx` strings consistently across product and fact tables.

---

## 🧪 What you can do with this dataset

- Measure promo lift by store/category/segment
- Analyze price elasticities using daily price history
  - Note: Available in v1_2025-09-21 (`daily_prices.csv`); use `notebooks/get_daily_prices.py` to regenerate for other versions.
- Study basket composition and size changes during promos
- Build forecasting and uplift models for promotions
- Teach joins, time windows, and event modeling with real‑ish data

---

🤝 Contributing
Issues and discussions welcome. Improvements to data and documentation are encouraged.

📚 License

Creative Commons CC BY 4.0 — share and adapt with attribution.

Full text: https://creativecommons.org/licenses/by/4.0/legalcode

Maintainer: Dr. Jose Mendoza — https://www.jose-mendoza.com

Last update: 2025-10-16
