#!/usr/bin/env python3
"""
validate_promos.py — Mancino Market promotions.csv validator

Checks:
- Exact 23-column header (canonical schema)
- Every row has 23 fields
- week_start parses, is a Sunday; week_end = week_start + 6
- promo_type ∈ {BOGO, BUNDLE, COUPON, MANAGER_SPECIAL}
- scope_type ∈ {sku, category}
- can_stack, active ∈ {TRUE, FALSE} (case-insensitive)
- Numeric fields parse and are sensible (>=0, integer where required)
- Type-specific required fields present (see rules below)
- Scope IDs exist in products.csv (sku_id or category_id), if provided
- store_scope either "ALL" or known store_id(s) from stores.csv, if provided
- Flags duplicate scopes in the same week (same week_start, scope_type, scope_id, store_scope, promo_type)

Exit codes:
  0 = OK (may include warnings)
  1 = Validation errors
  2 = Usage error

Usage (from repo root):
  python notebooks/validate_promos.py \
    ./data/v1_2025-08-24/promotions.csv \
    ./data/v1_2025-08-24/products.csv \
    ./data/v1_2025-08-24/stores.csv
"""

from __future__ import annotations
import sys, csv
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, Tuple, List, Dict

REQUIRED_HEADER = [
    "promotion_id","promo_type","name","week_start","week_end","scope_type","scope_id","store_scope",
    "amount_off","percent_off","buy_qty","get_qty","new_price","min_qty","min_spend",
    "bundle_type","bundle_qty","bundle_price","limit_per_customer","priority","can_stack","notes","active"
]

ALLOWED_PROMO_TYPES = {"BOGO","BUNDLE","COUPON","MANAGER_SPECIAL"}
ALLOWED_SCOPE_TYPES = {"sku","category"}
ALLOWED_BUNDLE_TYPES = {"mix_n_match","fixed_set"}

# --- Helpers -----------------------------------------------------------------

def usage() -> None:
    print("Usage: validate_promos.py <promotions.csv> [<products.csv>] [<stores.csv>]")
    print("Tip: pass products.csv to validate sku/category, and stores.csv to validate store_scope IDs.")
    sys.exit(2)

def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def is_sunday(d: date) -> bool:
    # Monday=0 ... Sunday=6
    return d.weekday() == 6

def parse_bool_str(s: str) -> Optional[bool]:
    if s is None: return None
    t = s.strip().lower()
    if t in {"true","t","1","yes","y"}: return True
    if t in {"false","f","0","no","n"}: return False
    return None

def parse_int(s: str) -> Optional[int]:
    if s.strip()=="":
        return None
    try:
        return int(s)
    except Exception:
        return None

def parse_float(s: str) -> Optional[float]:
    if s.strip()=="":
        return None
    try:
        return float(s)
    except Exception:
        return None

def load_ref_sets(products_path: Optional[Path], stores_path: Optional[Path]) -> Tuple[set, set, set]:
    sku_set, cat_set, store_set = set(), set(), set()
    if products_path and products_path.exists():
        with products_path.open(newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            fns = rdr.fieldnames or []
            sku_col = "sku_id" if "sku_id" in fns else None
            cat_col = "category_id" if "category_id" in fns else None
            for r in rdr:
                if sku_col and r.get(sku_col): sku_set.add(r[sku_col])
                if cat_col and r.get(cat_col): cat_set.add(r[cat_col])
    if stores_path and stores_path.exists():
        with stores_path.open(newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            fns = rdr.fieldnames or []
            st_col = "store_id" if "store_id" in fns else None
            for r in rdr:
                if st_col and r.get(st_col): store_set.add(r[st_col])
    return sku_set, cat_set, store_set

# --- Row validation -----------------------------------------------------------

def validate_row(rec: Dict[str,str],
                 line_no: int,
                 sku_set: set,
                 cat_set: set,
                 store_set: set) -> Tuple[List[str], List[str]]:
    """
    Returns (errors, warnings) for a single promotions row.
    """
    errs, warns = [], []

    # Required fields
    pid = rec["promotion_id"].strip()
    if not pid:
        errs.append(f"Line {line_no}: promotion_id is required")

    ptype = rec["promo_type"].strip()
    if ptype not in ALLOWED_PROMO_TYPES:
        errs.append(f"Line {line_no}: invalid promo_type '{ptype}'")

    scope_type = rec["scope_type"].strip()
    if scope_type not in ALLOWED_SCOPE_TYPES:
        errs.append(f"Line {line_no}: invalid scope_type '{scope_type}'")

    # Dates
    try:
        ws = parse_date(rec["week_start"])
        we = parse_date(rec["week_end"])
        if not is_sunday(ws):
            errs.append(f"Line {line_no}: week_start {ws} must be a Sunday")
        if (we - ws) != timedelta(days=6):
            errs.append(f"Line {line_no}: week_end {we} must equal week_start+6 days")
    except Exception as e:
        errs.append(f"Line {line_no}: invalid date(s) → {e}")
        # Bail early; subsequent checks depend on valid dates
        return errs, warns

    # Booleans
    for col in ("can_stack","active"):
        val = parse_bool_str(rec[col])
        if val is None:
            errs.append(f"Line {line_no}: {col} must be TRUE or FALSE")

    # Numbers (parse if provided)
    ints_pos = {"buy_qty","get_qty","min_qty","bundle_qty","limit_per_customer","priority"}
    floats_pos = {"amount_off","percent_off","new_price","min_spend","bundle_price"}

    parsed_ints = {}
    for c in ints_pos:
        if rec[c].strip() != "":
            iv = parse_int(rec[c])
            if iv is None or iv < 0:
                errs.append(f"Line {line_no}: {c} must be a non-negative integer")
            else:
                parsed_ints[c] = iv

    parsed_floats = {}
    for c in floats_pos:
        if rec[c].strip() != "":
            fv = parse_float(rec[c])
            if fv is None or fv < 0:
                errs.append(f"Line {line_no}: {c} must be a non-negative number")
            else:
                parsed_floats[c] = fv

    # Percent bounds
    if "percent_off" in parsed_floats:
        if not (0 < parsed_floats["percent_off"] <= 100):
            errs.append(f"Line {line_no}: percent_off must be in (0,100]")

    # Scope existence
    sid = rec["scope_id"].strip()
    if scope_type == "sku" and sku_set:
        if sid not in sku_set:
            errs.append(f"Line {line_no}: scope_id '{sid}' not found in products.sku_id")
    if scope_type == "category" and cat_set:
        if sid not in cat_set:
            errs.append(f"Line {line_no}: scope_id '{sid}' not found in products.category_id")

    # Store scope
    ss = rec["store_scope"].strip()
    if ss != "ALL" and store_set:
        for s in [x.strip() for x in ss.split(",") if x.strip()]:
            if s not in store_set:
                errs.append(f"Line {line_no}: unknown store_id in store_scope → '{s}'")

    # Type-specific rules
    if ptype == "BOGO":
        if "buy_qty" not in parsed_ints or "get_qty" not in parsed_ints:
            errs.append(f"Line {line_no}: BOGO needs buy_qty and get_qty")
        if parsed_ints.get("buy_qty", 0) == 0 or parsed_ints.get("get_qty", 0) == 0:
            errs.append(f"Line {line_no}: BOGO buy_qty/get_qty must be > 0")
    elif ptype == "COUPON":
        has_amt = "amount_off" in parsed_floats
        has_pct = "percent_off" in parsed_floats
        if not (has_amt ^ has_pct):  # exactly one
            errs.append(f"Line {line_no}: COUPON needs exactly one of amount_off or percent_off")
        # Optional: min_qty or min_spend ok if present
    elif ptype == "MANAGER_SPECIAL":
        has_new = "new_price" in parsed_floats
        has_pct = "percent_off" in parsed_floats
        if not (has_new or has_pct):
            errs.append(f"Line {line_no}: MANAGER_SPECIAL needs new_price or percent_off")
    elif ptype == "BUNDLE":
        bt = rec["bundle_type"].strip()
        if bt not in ALLOWED_BUNDLE_TYPES:
            errs.append(f"Line {line_no}: BUNDLE bundle_type must be one of {sorted(ALLOWED_BUNDLE_TYPES)}")
        if "bundle_qty" not in parsed_ints or parsed_ints.get("bundle_qty", 0) < 2:
            errs.append(f"Line {line_no}: BUNDLE needs bundle_qty >= 2")
        if "bundle_price" not in parsed_floats or parsed_floats.get("bundle_price", 0) <= 0:
            errs.append(f"Line {line_no}: BUNDLE needs bundle_price > 0")

    # Soft validations / warnings
    if rec["notes"].find(",") >= 0:
        warns.append(f"Line {line_no}: notes contains a comma; ensure the CSV stays 23 columns (quote if needed)")

    return errs, warns

# --- Main --------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args:
        usage()

    promos_path = Path(args[0])
    products_path = Path(args[1]) if len(args) > 1 else None
    stores_path   = Path(args[2]) if len(args) > 2 else None

    if not promos_path.exists():
        print(f"[ERROR] {promos_path} not found"); sys.exit(1)

    sku_set, cat_set, store_set = load_ref_sets(products_path, stores_path)

    with promos_path.open(newline="", encoding="utf-8") as f:
        rdr = csv.reader(f)
        try:
            header = next(rdr)
        except StopIteration:
            print("[ERROR] promotions.csv is empty"); sys.exit(1)

        if header != REQUIRED_HEADER:
            print("[ERROR] Header mismatch.")
            print("  Expected:", REQUIRED_HEADER)
            print("  Found:   ", header)
            sys.exit(1)

        ncols = len(header)
        rows = list(rdr)

    errors: List[str] = []
    warnings: List[str] = []
    seen_keys = set()  # detect duplicates within a week scope

    type_counts = {"BOGO":0,"BUNDLE":0,"COUPON":0,"MANAGER_SPECIAL":0}
    weeks = set()

    for i, row in enumerate(rows, start=2):
        if len(row) != ncols:
            errors.append(f"Line {i}: expected {ncols} columns, found {len(row)}")
            continue

        rec = dict(zip(REQUIRED_HEADER, row))

        e, w = validate_row(rec, i, sku_set, cat_set, store_set)
        errors.extend(e)
        warnings.extend(w)

        # Duplicate scope per week check (only if basic fields parsed)
        try:
            ws = rec["week_start"]
            key = (ws, rec["scope_type"], rec["scope_id"], rec["store_scope"], rec["promo_type"])
            if key in seen_keys:
                errors.append(f"Line {i}: duplicate promo for same week/scope/store/type → {key}")
            else:
                seen_keys.add(key)
            # Collect fast stats
            if rec["promo_type"] in type_counts:
                type_counts[rec["promo_type"]] += 1
            weeks.add(ws)
        except Exception:
            # ignore if malformed; already counted in validation
            pass

    # Report
    if errors:
        print("✖ Validation FAILED")
        print(f"- Errors   : {len(errors)}")
        print(f"- Warnings : {len(warnings)}")
        print("\nDetails:")
        for msg in errors:
            print("  -", msg)
        if warnings:
            print("\nWarnings:")
            for msg in warnings:
                print("  -", msg)
        sys.exit(1)

    print("✔ promotions.csv looks good!")
    if warnings:
        print(f"• Warnings: {len(warnings)} (non-fatal)")
        for msg in warnings:
            print("  -", msg)

    # Quick summary
    if weeks:
        weeks_sorted = sorted(weeks)
        print(f"• Weeks covered: {weeks_sorted[0]} → {weeks_sorted[-1]}  ({len(weeks)} week(s))")
    print("• Promo type counts:", ", ".join(f"{k}={v}" for k,v in type_counts.items()))

if __name__ == "__main__":
    main()
