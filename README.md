# 🛒 Mancino Market
## Synthetic Grocery Retail Dataset (Public, Data-Only)

Mancino Market is a fully synthetic grocery retail dataset set in Manhattan, NYC. It’s designed for teaching, analytics, and modeling—rich enough to feel real, safe enough to share.

---

## 🚀 What’s in v1.5 (2025-09-21)

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

## 🌆 About Mancino

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
└── v1_2025-09-21/
    ├── customers.csv
    ├── daily_prices.csv
    ├── product_store_inventory.csv
    ├── products.csv
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
| `promotions.csv` | Weekly promotions (header) | Types: BOGO, BUNDLE, COUPON, MANAGER_SPECIAL; scope, stacking, priority |
| `promotion_items.csv` | Promotion↔SKU links | Narrow a promotion to specific SKUs when `scope_type=sku` |
| `promotion_stores.csv` | Promotion↔Store links | Narrow a promotion to specific stores (alternative to `store_scope=ALL`) |
| `transactions.csv` | Transaction headers | Extends through 2025-09-21; includes net and tax fields |
| `transaction_line_items.csv` | Line items | One row per SKU in a transaction (totals reflect promos) |
| `transaction_promotions.csv` | Promotion audit | One row per applied promotion→line item with discount details |
| `daily_prices.csv` | Daily price history | Baseline price by store and SKU on a date |

---

## 📐 Schemas (key columns)

These reflect the public CSVs in `v1_2025-09-21`.

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
- promotion_id, promo_type, name, week_start, week_end, scope_type, scope_id, store_scope,
  amount_off, percent_off, buy_qty, get_qty, new_price, min_qty, min_spend,
  bundle_type, bundle_qty, bundle_price, limit_per_customer, priority, can_stack, notes, active
  - `bundle_type` values include `mix_n_match` and `fixed_set`.
  - `store_scope` is `ALL` or an ID list; normalized store links also exist in `promotion_stores.csv`.

### promotion_items.csv
- promotion_id, sku_id

### promotion_stores.csv
- promotion_id, store_id

### transactions.csv
- transaction_id, store_id, customer_id, txn_ts, channel, subtotal_cents, tax_cents, total_cents, __tid_num, net_sales

### transaction_promotions.csv
- transaction_id, line_item_id, promotion_id, qty_discounted, discount_amount, applied_price, rule_note

### daily_prices.csv
- store_id, sku_id, date, price

---

## 🔗 Joining tips (IDs and formats)

- Store IDs appear as both numeric (e.g., `1..5` in `stores.csv`, `daily_prices.csv`) and string-coded (e.g., `S0001` in `transactions.csv`, `product_store_inventory.csv`).
  - To join: either pad numeric IDs to `S000x` or strip the `S` prefix and left zeros to get an integer.
- Product/SKU IDs use `Pxxxxx` strings consistently across product and fact tables.

---

## 🧪 What you can do with this dataset

- Measure promo lift by store/category/segment
- Analyze price elasticities using daily price history
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

Last update: 2025-10-08
