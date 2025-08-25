# 📚 Mancino Market — Data Dictionary (v1_2025-08-24)

This document defines the schema for the Mancino Market synthetic dataset.  
All CSVs are UTF-8 encoded, comma-separated, and include a header row.

---

## Conventions & Standards
- **IDs:** Opaque strings (no meanings encoded). Primary keys are unique.  
- **Money:** Stored as *cents* (integers). Do not include currency symbols.  
- **Dates:** ISO-8601 `YYYY-MM-DD`.  
- **Timestamps:** Local time (America/New_York) in ISO format `YYYY-MM-DDTHH:MM:SS`.  
- **Booleans:** `TRUE`/`FALSE`.  
- **Nulls:** Empty cell (no `"NULL"` string).  
- **Geo:** `latitude`, `longitude` are WGS84 decimal degrees (6 fractional digits).  

---

## File List
1. `stores.csv` — Store master data  
2. `customers.csv` — Customer master data  
3. `products.csv` — Product catalog  
4. `product_store_inventory.csv` — Store assortment and inventory  
5. `transactions.csv` — Sales transaction headers  
6. `transaction_items.csv` — Sales transaction line items  
7. `meta.json` — Generation metadata (JSON; informational)  

---

## 1) stores.csv
**Primary Key:** `store_id`

| Column | Type | Description | Example |
|---|---|---|---|
| store_id | string | Unique store identifier | `S0001` |
| store_code | string | Human code | `MIDTOWN` |
| name | string | Display name | `Mancino Market – Midtown` |
| neighborhood | string | NYC neighborhood | `Midtown` |
| borough | string | NYC borough | `Manhattan` |
| address | string | Street address | `1350 6th Ave` |
| city | string | Always `New York` | `New York` |
| state | string | Always `NY` | `NY` |
| zip | string | 5-digit ZIP | `10019` |
| latitude | decimal(9,6) | WGS84 latitude | `40.764250` |
| longitude | decimal(9,6) | WGS84 longitude | `-73.978700` |
| opened_date | date | Store opening date | `2024-06-01` |
| store_type | string | Format / type | `Grocery – Urban Medium` |
| sqft | int | Square footage | `15000` |

---

## 2) customers.csv
**Primary Key:** `customer_id`  
**Foreign Key:** `home_store_id → stores.store_id`

| Column | Type | Description | Example |
|---|---|---|---|
| customer_id | string | Unique customer identifier | `C000123` |
| first_name | string | First name | `Alex` |
| last_name | string | Last name | `Garcia` |
| email | string | Unique email | `alex.garcia123@example.com` |
| phone | string | NANP phone | `(347) 555-0186` |
| address | string | Street address | `215 W 55th St` |
| city | string | Always `New York` | `New York` |
| state | string | Always `NY` | `NY` |
| zip | string | ZIP near home store | `10019` |
| latitude | decimal(9,6) | Geo coordinate inside neighborhood bbox | `40.762314` |
| longitude | decimal(9,6) | Geo coordinate inside neighborhood bbox | `-73.981442` |
| birth_date | date | 1945–2007 typical range | `1989-05-11` |
| gender | string | Optional; may be empty | `` |
| loyalty_tier | string | `None` / `Silver` / `Gold` / `Platinum` | `Silver` |
| signup_date | date | Account creation date | `2024-10-03` |
| marketing_opt_in | boolean | Opt-in flag | `TRUE` |
| home_store_id | string | Preferred store (FK) | `S0001` |

---

## 3) products.csv
**Primary Key:** `product_id`

| Column | Type | Description | Example |
|---|---|---|---|
| product_id | string | Unique product identifier | `P00042` |
| upc | string | 12-digit synthetic UPC | `100000000041` |
| brand | string | Brand name | `Mancino Private Label` |
| product_name | string | Consumer-facing name | `Mancino Private Label Yogurt 32 oz` |
| category | string | Top category | `Dairy & Eggs` |
| subcategory | string | Subcategory | `Yogurt` |
| size | string | Pack/size label | `32 oz` |
| unit_of_measure | string | Unit symbol | `oz` |
| base_price_cents | int | HQ/base list price | `499` |
| tax_code | string | `FOOD_NONTAX` / `FOOD_TAXABLE` / `ALCOHOL` | `FOOD_NONTAX` |
| is_perishable | boolean | TRUE for perishable | `TRUE` |
| is_age_restricted | boolean | TRUE for alcohol | `FALSE` |
| brand_tier | string | `Private Label` / `National` / `Premium` | `Private Label` |
| created_date | date | SKU inception | `2024-01-15` |

---

## 4) product_store_inventory.csv
**Primary Key:** `(store_id, product_id)`  
**Foreign Keys:** `store_id → stores.store_id`, `product_id → products.product_id`

| Column | Type | Description | Example |
|---|---|---|---|
| product_id | string | Product (FK) | `P00042` |
| store_id | string | Store (FK) | `S0001` |
| on_hand_units | int | Stock on hand (10–100) | `42` |
| reorder_point | int | Reorder threshold (10–30) | `20` |
| base_price_override_cents | int (nullable) | Store-level override price | `515` |
| active | boolean | Currently stocked | `TRUE` |

---

## 5) transactions.csv
**Primary Key:** `transaction_id`  
**Foreign Keys:** `store_id → stores.store_id`, `customer_id → customers.customer_id` (nullable)

| Column | Type | Description | Example |
|---|---|---|---|
| transaction_id | string | Unique transaction header ID | `T00012345` |
| store_id | string | Fulfillment store (FK) | `S0001` |
| customer_id | string (nullable) | Customer (FK) or empty | `C000987` |
| txn_ts | datetime | Timestamp (local time) | `2025-08-10T18:22:14` |
| subtotal_cents | int | Sum of item extended prices | `1899` |
| tax_cents | int | Sum of line taxes | `168` |
| total_cents | int | `subtotal + tax` | `2067` |
| payment_type | string | `Cash` / `Card` / `Mobile` | `Card` |
| channel | string | `In-Store` / `Online` | `In-Store` |
| promo_savings_cents | int | Promo savings (Phase 1: 0) | `0` |

---

## 6) transaction_items.csv
**Primary Key:** `transaction_item_id`  
**Unique Within Transaction:** `(transaction_id, line_number)`  
**Foreign Keys:** `transaction_id → transactions.transaction_id`, `product_id → products.product_id`, `store_id → stores.store_id`

| Column | Type | Description | Example |
|---|---|---|---|
| transaction_item_id | string | Unique line item ID | `T00012345-3` |
| transaction_id | string | Transaction (FK) | `T00012345` |
| line_number | int | 1..N | `3` |
| product_id | string | Purchased product (FK) | `P00042` |
| store_id | string | Denormalized store ID | `S0001` |
| unit_price_cents | int | Price at sale | `499` |
| quantity | int | Units purchased (≥1) | `2` |
| extended_price_cents | int | `unit_price_cents * quantity` | `998` |
| tax_cents | int | Per-line tax | `89` |
| promo_savings_cents | int | Promo savings (Phase 1: 0) | `0` |

---

## Enumerations
- **channel:** `In-Store`, `Online`  
- **payment_type:** `Cash`, `Card`, `Mobile`  
- **tax_code:** `FOOD_NONTAX`, `FOOD_TAXABLE`, `ALCOHOL`  
- **loyalty_tier:** `None`, `Silver`, `Gold`, `Platinum`  

---

## Suggested Indexes
- `transactions (txn_ts)` — time filtering  
- `transactions (store_id, txn_ts)` — store time-series  
- `transaction_items (transaction_id)` — join to headers  
- `transaction_items (store_id, product_id)` — item movement by store  
- `product_store_inventory (store_id, product_id)` — assortment lookup  
- `customers (home_store_id)` — neighborhood segmentation  

---

## Entity Relationships

stores (1) ──< product_store_inventory >── (1) products
│
├──< customers (home_store_id)
│
└──< transactions >──< transaction_items >── products

---

## QA Checklist
- Primary keys unique; foreign keys resolve.  
- Transaction totals reconcile with items.  
- `txn_ts` within `2025-07-01 → 2025-08-24`.  
- Monetary fields non-negative integers.  
- Customer and store coordinates valid in Manhattan bounds.  

---

## meta.json
Metadata file with dataset counts, time window, and seed.

**Example:**
```json
{
  "dataset": "Mancino Market",
  "version": "v1_2025-08-24",
  "seed": 424242,
  "customers": 5000,
  "stores": 5,
  "products": 2000,
  "inventory_rows": 8000,
  "transactions": 33000,
  "transaction_items": 200000,
  "time_window_start": "2025-07-01",
  "time_window_end": "2025-08-24",
  "channels": ["In-Store","Online"]
}
