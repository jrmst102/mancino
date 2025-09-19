#!/usr/bin/env python3
"""
mancino_summary.py
Summarize the latest Mancino dataset version.

Outputs:
- # Customers
- # Products
- # Categories
- # Transactions
- Date of last transaction
- # Promotions
- Date of last promotions (latest promo week)

Usage:
    python mancino_summary.py
    python mancino_summary.py --data-root ./data
    python mancino_summary.py --version v1_2025-09-21
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

VERSION_PATTERN = re.compile(r"^v1_\d{4}-\d{2}-\d{2}$")

POSSIBLE_TXN_DATE_COLS = [
    "txn_ts", "transaction_ts", "transaction_time", "transaction_datetime",
    "txn_date", "date", "transaction_date"
]

def find_latest_version_dir(data_root: Path) -> Path:
    """Pick the lexicographically latest folder matching v1_YYYY-MM-DD."""
    candidates = [p for p in data_root.iterdir() if p.is_dir() and VERSION_PATTERN.match(p.name)]
    if not candidates:
        raise FileNotFoundError(f"No versioned folders like v1_YYYY-MM-DD found under {data_root}")
    # Lexicographic works because YYYY-MM-DD sorts correctly as a string
    return sorted(candidates, key=lambda p: p.name)[-1]

def load_csv_safe(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)

def parse_latest_txn_date(df_txn: pd.DataFrame):
    if df_txn.empty:
        return None
    # Find a plausible datetime column
    date_col = None
    for c in POSSIBLE_TXN_DATE_COLS:
        if c in df_txn.columns:
            date_col = c
            break
    if date_col is None:
        # Try to infer: pick the first column with 'date' or 'time' in the name
        for c in df_txn.columns:
            cl = c.lower()
            if "date" in cl or "time" in cl:
                date_col = c
                break
    if date_col is None:
        return None
    # Parse to datetime (both date and datetime will work)
    try:
        dt = pd.to_datetime(df_txn[date_col], errors="coerce", utc=True)
        if dt.notna().any():
            # Convert to date (local-naive) for display
            last_dt = dt.max()
            # Show as YYYY-MM-DD
            return last_dt.date().isoformat()
        return None
    except Exception:
        return None

def parse_latest_promo_week(df_promos: pd.DataFrame):
    """Return a string for the latest promotions week, based on week_start/week_end."""
    if df_promos.empty:
        return None
    # Accept either strings or already-parsed dates
    for col in ["week_start", "week_end"]:
        if col in df_promos.columns:
            df_promos[col] = pd.to_datetime(df_promos[col], errors="coerce").dt.date
    if "week_start" not in df_promos.columns:
        return None
    # Filter to active if column exists, else use all
    df = df_promos
    if "active" in df.columns:
        # Accept various casings/values; coerce to bool
        def to_bool(x):
            if isinstance(x, bool):
                return x
            if pd.isna(x):
                return False
            s = str(x).strip().lower()
            return s in {"true", "1", "t", "yes", "y"}
        df = df[df["active"].map(to_bool)]
        if df.empty:
            df = df_promos  # fall back to all if no actives
    latest_start = df["week_start"].max()
    # If week_end exists, use it for range display
    if "week_end" in df.columns and pd.notna(df["week_end"]).any():
        latest_row = df.loc[df["week_start"] == latest_start].head(1)
        end_val = latest_row["week_end"].iloc[0] if "week_end" in latest_row.columns else None
        if pd.notna(end_val):
            return f"{latest_start.isoformat()} to {end_val.isoformat()}"
    return latest_start.isoformat()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=Path("data"), help="Root folder that contains version folders")
    ap.add_argument("--version", type=str, default=None, help="Specific version folder name (e.g., v1_2025-09-21)")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    data_root: Path = args.data_root

    if args.version:
        version_dir = data_root / args.version
        if not version_dir.exists():
            raise FileNotFoundError(f"{version_dir} not found")
    else:
        version_dir = find_latest_version_dir(data_root)

    # File paths
    p_customers = version_dir / "customers.csv"
    p_products = version_dir / "products.csv"
    p_transactions = version_dir / "transactions.csv"
    p_promotions = version_dir / "promotions.csv"

    # Load
    df_customers = load_csv_safe(p_customers)
    df_products = load_csv_safe(p_products)
    df_transactions = load_csv_safe(p_transactions)
    df_promotions = load_csv_safe(p_promotions)

    # Counts
    n_customers = df_customers["customer_id"].nunique() if "customer_id" in df_customers.columns else len(df_customers)
    n_products  = df_products["sku_id"].nunique() if "sku_id" in df_products.columns else len(df_products)

    # Categories (try common column names)
    cat_cols = [c for c in ["category_id", "category", "category_code"] if c in df_products.columns]
    if cat_cols:
        n_categories = df_products[cat_cols[0]].nunique()
    else:
        n_categories = None

    n_transactions = df_transactions["transaction_id"].nunique() if "transaction_id" in df_transactions.columns else len(df_transactions)

    # Dates
    last_txn_date = parse_latest_txn_date(df_transactions)
    n_promotions = len(df_promotions) if not df_promotions.empty else 0
    last_promo_week = parse_latest_promo_week(df_promotions)

    result = {
        "version_dir": str(version_dir),
        "customers_count": int(n_customers) if n_customers is not None else None,
        "products_count": int(n_products) if n_products is not None else None,
        "categories_count": int(n_categories) if n_categories is not None else None,
        "transactions_count": int(n_transactions) if n_transactions is not None else None,
        "last_transaction_date": last_txn_date,
        "promotions_count": int(n_promotions),
        "last_promotions": last_promo_week
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("\nMancino Market — Dataset Summary")
        print(f"Version folder:     {result['version_dir']}")
        print(f"Customers:          {result['customers_count']}")
        print(f"Products:           {result['products_count']}")
        print(f"Categories:         {result['categories_count']}")
        print(f"Transactions:       {result['transactions_count']}")
        print(f"Last transaction:   {result['last_transaction_date'] or 'N/A'}")
        print(f"Promotions:         {result['promotions_count']}")
        print(f"Last promotions:    {result['last_promotions'] or 'N/A'}")
        print("")

if __name__ == "__main__":
    main()
