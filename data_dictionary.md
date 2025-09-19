📚 Mancino Market — Data Dictionary (v1_2025-09-21)

This document defines the schema for the **Mancino Market** synthetic grocery dataset.  
All CSVs are UTF-8 encoded, comma-separated, and include a header row.

---

## Conventions & Standards

- **IDs:** Strings (no meanings encoded). Primary keys are unique.
- **Money:** Stored as two-decimal **USD** numbers (e.g., `12.34`). Totals reconcile: `subtotal + tax = total`.
- **Dates:** ISO-8601 `YYYY-MM-DD`.
- **Timestamps:** Local New York time (`America/New_York`) in `YYYY-MM-DD HH:MM:SS`.
- **Booleans:** `TRUE` / `FALSE` (case-insensitive).
- **Nulls:** Empty cell (no `"NULL"` literal).
- **Weeks:** Promotions use **Sunday→Saturday** windows. `week_start` is a **Sunday**.

> **Coverage:** Transactions extend **through 2025-09-21** (previous versions end at 2025-08-24).

---

## Files in `data/v1_2025-09-21/`

1. `stores.csv` — Store master data  
2. `customers.csv` — Customer master data  
3. `products.csv` — Product catalog  
4. `product_store_inventory.csv` — Store×SKU inventory (starting levels)  
5. `promotions.csv` — **Weekly promotions (v1.5)**  
6. `transactions.csv` — Sales transaction headers  
7. `transaction_line_items.csv` — Sales transaction line items  
8. `transaction_promotions.csv` — **Promo audit (applied rules per line)**  
9. `inventory_events.csv` — **Stockout & replenishment events**

---

## 1) `stores.csv`

**Primary Key:** `store_id`

| Column       | Type            | Description                         | Example                     |
|--------------|-----------------|-------------------------------------|-----------------------------|
| store_id     | string          | Unique store identifier             | `S0004`                     |
| store_code   | string          | Human-friendly code                 | `CHELSEA`                   |
| store_name   | string          | Display name                        | `Mancino Market – Chelsea`  |
| neighborhood | string          | NYC neighborhood                    | `Chelsea`                   |
| borough      | string          | NYC borough                         | `Manhattan`                 |
| address      | string          | Street address                      | `250 W 23rd St`             |
| city         | string          | Always `New York`                   | `New York`                  |
| state        | string          | Always `NY`                         | `NY`                        |
| zip          | string          | 5-digit ZIP                         | `10011`                     |
| latitude     | decimal(9,6)    | WGS84 latitude                      | `40.744120`                 |
| longitude    | decimal(9,6)    | WGS84 longitude                     | `-73.997650`                |
| opened_date  | date            | Store opening date                  | `2024-06-01`                |
| store_type   | string          | Format / type                       | `Grocery – Urban Medium`    |
| sqft         | int             | Approx. square footage              | `15000`                     |

---

## 2) `customers.csv`

**Primary Key:** `customer_id`  
**Foreign Key:** `home_store_id → stores.store_id` (optional)

| Column          | Type           | Description                                  | Example                          |
|-----------------|----------------|----------------------------------------------|----------------------------------|
| customer_id     | string         | Unique customer identifier                    | `C004237`                        |
| first_name      | string         | First name                                    | `Alex`                           |
| last_name       | string         | Last name                                     | `Garcia`                         |
| email           | string         | Email (synthetic)                             | `alex.garcia@example.com`        |
| phone           | string         | NANP phone                                    | `(347) 555-0186`                 |
| address         | string         | Street address                                | `215 W 55th St`                  |
| city            | string         | Always `New York`                             | `New York`                       |
| state           | string         | Always `NY`                                   | `NY`                             |
| zip             | string         | ZIP near home store                           | `10019`                          |
| latitude        | decimal(9,6)   | Geocoordinate (synthetic)                     | `40.762314`                      |
| longitude       | decimal(9,6)   | Geocoordinate (synthetic)                     | `-73.981442`                     |
| birth_date      | date           | Typical range 1945–2007                       | `1989-05-11`                     |
| gender          | string         | Optional                                      |                                  |
| loyalty_tier    | string         | `None` / `Silver` / `Gold` / `Platinum`       | `Silver`                         |
| signup_date     | date           | Account creation date                         | `2024-10-03`                     |
| marketing_opt_in| boolean        | Email/SMS opt-in flag                         | `TRUE`                           |
| home_store_id   | string         | Preferred store (FK, optional)                | `S0001`                          |

---

## 3) `products.csv`

**Primary Key:** `product_id` (alias used in some tooling: **`sku_id`**)

| Column              | Type          | Description                                | Example                                |
|---------------------|---------------|--------------------------------------------|----------------------------------------|
| product_id          | string        | Unique product identifier                  | `P001234`                              |
| upc                 | string        | Synthetic 12-digit UPC                     | `100000120345`                         |
| brand               | string        | Brand                                      | `Mancino Private Label`                |
| product_name        | string        | Consumer-facing name                       | `Yogurt 32 oz Plain`                   |
| category            | string        | Top category                               | `Dairy & Eggs`                         |
| subcategory         | string        | Subcategory                                | `Yogurt`                               |
| size                | string        | Pack/size label                            | `32 oz`                                |
| unit_of_measure     | string        | Unit symbol                                | `oz`                                   |
| price               | decimal(10,2) | Base/store-agnostic price (USD)            | `4.99`                                 |
| tax_code            | string        | `FOOD_NONTAX` / `FOOD_TAXABLE` / `ALCOHOL` | `FOOD_NONTAX`                          |
| is_perishable       | boolean       | TRUE if perishable                         | `TRUE`                                 |
| is_age_restricted   | boolean       | TRUE for alcohol                           | `FALSE`                                |
| brand_tier          | string        | `Private Label` / `National` / `Premium`   | `Private Label`                        |
| created_date        | date          | SKU inception date                          | `2024-01-15`                           |

> **Note:** Some pipelines refer to `sku_id`. Treat `sku_id` as the same logical key as `product_id`.

---

## 4) `product_store_inventory.csv`

**Primary Key:** `(store_id, product_id)` (alias accepted: `sku_id`)  
**Foreign Keys:** `store_id → stores.store_id`, `product_id → products.product_id`

| Column              | Type           | Description                                   | Example  |
|---------------------|----------------|-----------------------------------------------|----------|
| store_id            | string         | Store (FK)                                    | `S0003`  |
| product_id / sku_id | string         | Product (FK)                                  | `P001234`|
| on_hand / on_hand_units | int        | Units on hand at start of simulation          | `42`     |
| reorder_point       | int (optional) | Reorder threshold                             | `20`     |
| base_price_override | decimal(10,2) (optional) | Store-level price override           | `5.15`   |
| active              | boolean        | Is actively stocked                           | `TRUE`   |

> Column names may vary slightly across versions. The presence of **store**, **product (SKU)**, and an **on-hand quantity** is essential.

---

## 5) `promotions.csv`  **(v1.5)**

**Primary Key:** `promotion_id`  
**Granularity:** Weekly promotions (Sunday→Saturday), scoped by SKU or Category, optionally store-specific.

| Column              | Type            | Description                                                                                  | Example                           |
|---------------------|-----------------|----------------------------------------------------------------------------------------------|-----------------------------------|
| promotion_id        | string          | Unique promotion ID                                                                          | `PR-2025-09-14-012`               |
| promo_type          | enum            | `BOGO` / `BUNDLE` / `COUPON` / `MANAGER_SPECIAL`                                             | `COUPON`                          |
| name                | string          | Short description                                                                            | `5% off Cheese`                   |
| week_start          | date (Sunday)   | First day of the promo week                                                                  | `2025-09-14`                      |
| week_end            | date (Saturday) | Last day of the promo week                                                                   | `2025-09-20`                      |
| scope_type          | enum            | `sku` / `category`                                                                           | `category`                        |
| scope_id            | string          | SKU or Category identifier                                                                   | `Dairy & Eggs`                    |
| store_scope         | string          | `ALL` or comma-separated store IDs                                                           | `ALL`                             |
| amount_off          | decimal(10,2)   | Flat discount (USD)                                                                          | `1.00`                            |
| percent_off         | decimal(5,2)    | Percent discount                                                                             | `10`                              |
| buy_qty             | int             | For BOGO (buy X)                                                                             | `1`                               |
| get_qty             | int             | For BOGO (get Y free)                                                                        | `1`                               |
| new_price           | decimal(10,2)   | For manager special (set price)                                                              | `2.99`                            |
| min_qty             | int             | For coupon thresholds                                                                        | `2`                               |
| min_spend           | decimal(10,2)   | For coupon thresholds (USD)                                                                  | `10.00`                           |
| bundle_type         | string          | Bundle rule label (informational)                                                            | `ANY`                             |
| bundle_qty          | int             | Units per bundle                                                                             | `3`                               |
| bundle_price        | decimal(10,2)   | Price for the bundle                                                                         | `10.00`                           |
| limit_per_customer  | int             | Per-customer limit within the week                                                           | `0` (=no limit)                   |
| priority            | int             | Higher priority overrides lower when overlapping                                             | `10`                              |
| can_stack           | boolean         | Whether this promo can stack with others                                                     | `FALSE`                           |
| notes               | string          | Free-text notes                                                                              | `Cheese Week`                     |
| active              | boolean         | Include/exclude row                                                                          | `TRUE`                            |

---

## 6) `transactions.csv`

**Primary Key:** `transaction_id`  
**Foreign Keys:** `store_id → stores.store_id`; `customer_id → customers.customer_id` (nullable)

| Column         | Type            | Description                                 | Example                 |
|----------------|-----------------|---------------------------------------------|-------------------------|
| transaction_id | string          | Unique transaction header ID                | `T1726765021`           |
| store_id       | string          | Store where the sale occurred               | `S0002`                 |
| customer_id    | string (nullable)| Loyalty customer (if matched)              | `C004237`               |
| txn_ts         | datetime        | Local timestamp `YYYY-MM-DD HH:MM:SS`       | `2025-09-14 13:26:44`   |
| subtotal       | decimal(10,2)   | Sum of **post-promo** line totals           | `18.99`                 |
| tax            | decimal(10,2)   | Tax at point of sale                        | `1.69`                  |
| total          | decimal(10,2)   | `subtotal + tax`                            | `20.68`                 |

---

## 7) `transaction_line_items.csv`

**Primary Key:** `line_item_id`  
**Foreign Keys:** `transaction_id → transactions.transaction_id`; `product_id/sku_id → products.product_id`; `store_id → stores.store_id`

| Column        | Type            | Description                                                   | Example       |
|---------------|-----------------|---------------------------------------------------------------|---------------|
| transaction_id| string          | Transaction header (FK)                                      | `T1726765021` |
| line_item_id  | string          | Unique line ID                                               | `L000000123`  |
| store_id      | string          | Denormalized store ID                                        | `S0002`       |
| product_id / sku_id | string    | Item sold (FK)                                               | `P001234`     |
| qty           | int             | Units sold (≥1)                                              | `2`           |
| unit_price    | decimal(10,2)   | Pre-discount unit price at time of sale                      | `4.99`        |
| line_total    | decimal(10,2)   | **Post-promo** extended price used in `subtotal`             | `8.98`        |

> Per-line promo details are captured in `transaction_promotions.csv`.

---

## 8) `transaction_promotions.csv`  **(v1.5)**

**Grain:** One row per **applied promotion × line item**.

| Column          | Type            | Description                                      | Example         |
|-----------------|-----------------|--------------------------------------------------|-----------------|
| transaction_id  | string          | Transaction (FK)                                 | `T1726765021`   |
| line_item_id    | string          | Line item (FK)                                   | `L000000123`    |
| promotion_id    | string          | Promotion applied                                | `PR-2025-09-14-012` |
| qty_discounted  | int             | Quantity receiving discount                      | `1`             |
| discount_amount | decimal(10,2)   | USD discount allocated to this line              | `1.00`          |
| applied_price   | decimal(10,2)   | Effective unit price after promotion             | `3.99`          |
| rule_note       | string          | Mechanic applied (`BOGO`, `BUNDLE`, etc.)        | `BUNDLE`        |

---

## 9) `inventory_events.csv`  **(v1.5)**

**Grain:** Inventory events produced during simulation (stockouts during sales and nightly replenishments).

| Column     | Type            | Description                                        | Example               |
|------------|-----------------|----------------------------------------------------|-----------------------|
| event_id   | string          | Unique event ID                                    | `E10234`              |
| store_id   | string          | Store (FK)                                         | `S0003`               |
| product_id / sku_id | string | Product (FK)                                       | `P001234`             |
| event_ts   | datetime        | Local timestamp `YYYY-MM-DD HH:MM:SS`              | `2025-09-14 13:27:02` |
| event_type | enum            | `STOCKOUT` / `REPLENISHMENT`                       | `STOCKOUT`            |
| qty        | int             | Positive quantity (units)                          | `1`                   |
| reason     | string          | Cause/context                                      | `during_txn` / `EOD`  |
| ref        | string          | Reference (`transaction_id` or `EOD`)              | `T1726765021`         |

---

## Enumerations

- **promo_type:** `BOGO`, `BUNDLE`, `COUPON`, `MANAGER_SPECIAL`  
- **event_type:** `STOCKOUT`, `REPLENISHMENT`  
- **tax_code:** `FOOD_NONTAX`, `FOOD_TAXABLE`, `ALCOHOL`  
- **loyalty_tier:** `None`, `Silver`, `Gold`, `Platinum`

---

## Keys & Relationships

stores (1) ──< customers (home_store_id optional)
│
├──< product_store_inventory >── (1) products
│ ▲
└──< transactions >──< transaction_line_items >───┘
│
└──< transaction_promotions (per applied rule)
products ↔ inventory_events (product_id/sku_id, store_id) [events reference items by store/SKU]


---

## QA Checklist (v1_2025-09-21)

- Primary keys unique; foreign keys resolve across all files.  
- `subtotal + tax = total` for every row in `transactions.csv`.  
- `line_total` values sum to `subtotal` per transaction.  
- Timestamps fall within dataset window (ending **2025-09-21**).  
- Promotions weeks begin on **Sundays** and match `week_end` (Saturday).  
- `inventory_events.csv` only contains `STOCKOUT` or `REPLENISHMENT`.  

---

_Last updated: 2025-09-21_
