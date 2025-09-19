#!/usr/bin/env python3
"""
Generate weekly promotions for Mancino Market.

- Weeks always start on Sunday and last 7 days (Sun..Sat).
- Creates 12–18 promos per week by default, with a uniform variety of:
  BOGO, BUNDLE, COUPON, MANAGER_SPECIAL.
- Uses real category IDs from products.csv and real stores from stores.csv.
- For bundles, estimates bundle_price from category median unit price.

Usage examples (run from repo root):
  python code/utils/generate_promos.py \
      --data-root ./data --version v1_2025-08-24 \
      --start 2025-08-25 --end 2025-09-21 \
      --min 12 --max 18 --seed 42

You can re-run safely; it appends new IDs and leaves existing rows intact.
"""

from __future__ import annotations
import argparse, random, sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

PROMO_HEADER = [
    "promotion_id","promo_type","name","week_start","week_end","scope_type","scope_id","store_scope",
    "amount_off","percent_off","buy_qty","get_qty","new_price","min_qty","min_spend",
    "bundle_type","bundle_qty","bundle_price","limit_per_customer","priority","can_stack","notes","active"
]

PRICE_COL_CANDIDATES = ["price","unit_price","base_price","list_price","msrp"]

def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def sunday_on_or_before(d: date) -> date:
    # Python weekday: Mon=0..Sun=6 → subtract (weekday+1)%7 to get prior Sunday (or same if Sunday)
    return d - timedelta(days=(d.weekday()+1) % 7)

def sundays_between(start_d: date, end_d: date) -> List[date]:
    first_sun = sunday_on_or_before(start_d)
    last_sun  = sunday_on_or_before(end_d)
    out = []
    cur = first_sun
    while cur <= last_sun:
        out.append(cur)
        cur += timedelta(days=7)
    return out

def load_products(products_path: Path) -> pd.DataFrame:
    df = pd.read_csv(products_path)
    # Pick a category column
    cat_col = None
    for c in ["category_id","category","category_code","category_name"]:
        if c in df.columns:
            cat_col = c
            break
    if cat_col is None:
        raise ValueError(f"No category column found in {products_path} (expected one of category_id/category/...)")
    df["_category_col"] = cat_col

    # Find a price column if any
    price_col = None
    for c in PRICE_COL_CANDIDATES:
        if c in df.columns:
            price_col = c
            break
    df["_price_col"] = price_col
    return df

def load_stores(stores_path: Path) -> List[str]:
    if not stores_path.exists():
        return []
    df = pd.read_csv(stores_path)
    sid = "store_id" if "store_id" in df.columns else None
    return df[sid].dropna().astype(str).unique().tolist() if sid else []

def ensure_promotions_file(path: Path):
    if not path.exists():
        path.write_text(",".join(PROMO_HEADER) + "\n", encoding="utf-8")

def pick_types_uniform(n: int) -> List[str]:
    types = ["BOGO","BUNDLE","COUPON","MANAGER_SPECIAL"]
    out = []
    i = 0
    while len(out) < n:
        out.append(types[i % 4])
        i += 1
    # shuffle within week for variety
    random.shuffle(out)
    return out[:n]

def median_price_for_category(df_prod: pd.DataFrame, category_id, cat_col: str) -> Optional[float]:
    price_col = df_prod["_price_col"].iloc[0]
    if not price_col:
        return None
    ser = df_prod.loc[df_prod[cat_col] == category_id, price_col]
    try:
        ser = pd.to_numeric(ser, errors="coerce").dropna()
        if len(ser):
            return float(ser.median())
    except Exception:
        pass
    return None

def build_promo_row(week_start: date, ptype: str, scope_id: str, store_scope: str,
                    base_price: Optional[float], seq: int) -> List[str]:
    ws = week_start
    we = ws + timedelta(days=6)
    pid = f"PR{ws.strftime('%Y%m%d')}{seq:02d}"
    # Defaults
    amount_off = ""
    percent_off = ""
    buy_qty = ""
    get_qty = ""
    new_price = ""
    min_qty = ""
    min_spend = ""
    bundle_type = ""
    bundle_qty = ""
    bundle_price = ""
    limit_per_customer = str(random.choice([4,6,8,10]))
    priority = {"BUNDLE":"90","BOGO":"80","COUPON":"70","MANAGER_SPECIAL":"60"}[ptype]
    can_stack = "TRUE" if ptype in ("COUPON","MANAGER_SPECIAL") else "FALSE"
    notes = ""
    name = ""

    # Reasonable defaults by type; notes have no commas
    if ptype == "BOGO":
        buy_qty, get_qty = "1", "1"
        name = "Buy 1 Get 1"
        notes = "applies to category; singles only"
    elif ptype == "COUPON":
        # ~10–30% typical: choose either $ or %
        if base_price and base_price > 0:
            # amount_off ~ 10–25% of base_price
            ao = round(random.choice([0.5,1.0,1.5,2.0,2.5,3.0]), 2)
            amount_off = f"{ao:.2f}"
            min_spend = random.choice(["", "10.00", "12.00", "15.00"])
            name = f"${amount_off} Off (coupon)"
        else:
            percent_off = random.choice(["10","15","20","25"])
            min_qty = random.choice(["","2","3"])
            name = f"{percent_off}% Off (coupon)"
        notes = "coupon applies at checkout"
    elif ptype == "MANAGER_SPECIAL":
        # Prefer percent_off if no reliable base price
        if base_price and base_price > 0:
            percent_off = random.choice(["15","20","25"])
        else:
            percent_off = random.choice(["10","15","20","25"])
        name = f"Manager Special {percent_off}% Off"
        notes = "limited time markdown"
    elif ptype == "BUNDLE":
        bundle_type = random.choice(["mix_n_match","fixed_set"])
        bq = random.choice([2,3])
        bundle_qty = str(bq)
        # Estimate bundle price at ~20–30% off total median
        if base_price and base_price > 0:
            disc = random.choice([0.70,0.75,0.80])
            bp = round(bq * base_price * disc, 2)
        else:
            bp = 10.00 if bq == 3 else 6.00
        bundle_price = f"{bp:.2f}"
        name = f"{bundle_qty} for ${bundle_price}"
        notes = "mix and match allowed" if bundle_type=="mix_n_match" else "select set"
    else:
        raise ValueError(ptype)

    row = [
        pid, ptype, name, ws.isoformat(), we.isoformat(),
        "category", str(scope_id), store_scope,
        amount_off, percent_off, buy_qty, get_qty, new_price, min_qty, min_spend,
        bundle_type, bundle_qty, bundle_price,
        limit_per_customer, priority, can_stack, notes, "TRUE"
    ]
    assert len(row) == len(PROMO_HEADER)
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data"))
    ap.add_argument("--version", required=True, help="version folder under data/, e.g. v1_2025-08-24")
    ap.add_argument("--start", required=True, help="start date (YYYY-MM-DD)")
    ap.add_argument("--end", required=True, help="end date (YYYY-MM-DD)")
    ap.add_argument("--min", type=int, default=12, dest="per_min")
    ap.add_argument("--max", type=int, default=18, dest="per_max")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)

    version_dir = args.data_root / args.version
    products_path = version_dir / "products.csv"
    stores_path   = version_dir / "stores.csv"
    promos_path   = version_dir / "promotions.csv"

    if not version_dir.exists():
        sys.exit(f"[ERROR] {version_dir} not found")
    if not products_path.exists():
        sys.exit(f"[ERROR] products.csv not found at {products_path}")

    df_prod = load_products(products_path)
    cat_col = df_prod["_category_col"].iloc[0]
    categories = (
        df_prod[cat_col].dropna().astype(str).value_counts().index.tolist()
    )
    if not categories:
        sys.exit("[ERROR] No categories found in products.csv")

    # Median price per category (if price column exists)
    cat_median_price: Dict[str,float] = {}
    for c in categories:
        mp = median_price_for_category(df_prod, c, cat_col)
        if mp:
            cat_median_price[str(c)] = mp

    stores = load_stores(stores_path)
    has_stores = len(stores) > 0

    ensure_promotions_file(promos_path)

    start_d = parse_date(args.start)
    end_d   = parse_date(args.end)
    weeks = sundays_between(start_d, end_d)
    if not weeks:
        sys.exit("[ERROR] No Sunday-start weeks in the given range")

    rows_to_append: List[List[str]] = []

    for ws in weeks:
        # Decide how many promos this week
        n = random.randint(args.per_min, args.per_max)
        types = pick_types_uniform(n)

        # Pick categories (with repetition allowed but try to spread)
        # Shuffle the category list for variety week to week
        cats = categories.copy()
        random.shuffle(cats)
        cat_idx = 0

        seq = 1
        for ptype in types:
            # Cycle through categories to spread coverage
            if cat_idx >= len(cats):
                random.shuffle(cats)
                cat_idx = 0
            scope_id = cats[cat_idx]; cat_idx += 1

            # Store scope: ~1/3 store-specific if we have store list
            if has_stores and random.random() < 0.34:
                store_scope = random.choice(stores)
            else:
                store_scope = "ALL"

            base_price = cat_median_price.get(str(scope_id))
            row = build_promo_row(ws, ptype, scope_id, store_scope, base_price, seq)
            rows_to_append.append(row)
            seq += 1

    # Append to file
    with promos_path.open("a", encoding="utf-8") as f:
        for r in rows_to_append:
            f.write(",".join(r) + "\n")

    print(f"✔ Wrote {len(rows_to_append)} promotions to {promos_path}")
    print("Weeks covered:", ", ".join(w.isoformat() for w in weeks))
    # Show a small preview
    print("\nPreview:")
    for r in rows_to_append[:5]:
        print(",".join(r))

if __name__ == "__main__":
    main()
