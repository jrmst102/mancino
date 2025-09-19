#!/usr/bin/env python3
"""
normalize_promos.py — fix priority and store_scope in promotions.csv

- Sets default priority (if blank/invalid): BUNDLE=90, BOGO=80, COUPON=70, MANAGER_SPECIAL=60
- Normalizes store_scope to valid store_id(s) from stores.csv; supports:
    * exact id match (case-insensitive)
    * store_name -> store_id mapping (if stores.csv has store_name)
- Backs up promotions.csv as promotions.csv.bak

Usage (from repo root):
  python notebooks/normalize_promos.py \
    --promos ./data/v1_2025-09-21/promotions.csv \
    --stores ./data/v1_2025-09-21/stores.csv
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path

HEADER = [
    "promotion_id","promo_type","name","week_start","week_end","scope_type","scope_id","store_scope",
    "amount_off","percent_off","buy_qty","get_qty","new_price","min_qty","min_spend",
    "bundle_type","bundle_qty","bundle_price","limit_per_customer","priority","can_stack","notes","active"
]

DEFAULT_PRIORITY = {"BUNDLE":"90","BOGO":"80","COUPON":"70","MANAGER_SPECIAL":"60"}

def load_store_maps(stores_path: Path):
    """Return (valid_ids, name_to_id) where matches are case-insensitive."""
    valid_ids = set()
    name_to_id = {}
    with stores_path.open(newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        fns = rdr.fieldnames or []
        id_col = "store_id" if "store_id" in fns else None
        name_col = "store_name" if "store_name" in fns else None
        if not id_col:
            print("[ERROR] stores.csv missing store_id column", file=sys.stderr)
            sys.exit(1)
        for r in rdr:
            sid = (r.get(id_col) or "").strip()
            if not sid:
                continue
            valid_ids.add(sid)
            if name_col and r.get(name_col):
                name_to_id[r[name_col].strip().lower()] = sid
    # also allow id itself (case-insensitive) to map to id
    for sid in list(valid_ids):
        name_to_id[sid.lower()] = sid
    return valid_ids, name_to_id

def normalize_store_scope(value: str, valid_ids: set, name_to_id: dict):
    """Return (normalized_value, unresolved_tokens:list)."""
    v = (value or "").strip()
    if v == "" or v.upper() == "ALL":
        return "ALL", []
    toks = [t.strip() for t in v.split(",") if t.strip()]
    out = []
    unresolved = []
    seen = set()
    for t in toks:
        key = t.lower()
        sid = None
        if key in name_to_id:
            sid = name_to_id[key]
        # accept unique prefix match on id or name
        if not sid:
            candidates = [name_to_id[k] for k in name_to_id.keys() if k.startswith(key)]
            candidates = list(dict.fromkeys(candidates))  # dedupe preserving order
            if len(candidates) == 1:
                sid = candidates[0]
        if sid and sid in valid_ids:
            if sid not in seen:
                out.append(sid)
                seen.add(sid)
        else:
            unresolved.append(t)
    return (",".join(out) if out else value), unresolved

def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--promos", required=True, help="path to promotions.csv")
    ap.add_argument("--stores", required=True, help="path to stores.csv")
    args = ap.parse_args()

    promos_path = Path(args.promos)
    stores_path = Path(args.stores)
    if not promos_path.exists(): sys.exit(f"[ERROR] {promos_path} not found")
    if not stores_path.exists(): sys.exit(f"[ERROR] {stores_path} not found")

    valid_ids, name_to_id = load_store_maps(stores_path)

    with promos_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows: sys.exit("[ERROR] promotions.csv is empty")

    header = rows[0]
    if header != HEADER:
        print("[ERROR] Header mismatch in promotions.csv", file=sys.stderr)
        print("  Expected:", HEADER, file=sys.stderr)
        print("  Found   :", header, file=sys.stderr)
        sys.exit(1)

    fixed = [HEADER]
    unresolved_notes = []
    changed_priority = 0
    changed_stores = 0

    for i, row in enumerate(rows[1:], start=2):
        if len(row) != len(HEADER):
            print(f"[WARN] Line {i}: has {len(row)} columns (expected 23). Consider running your fixer first.", file=sys.stderr)
            # pad/truncate to 23 to avoid index errors
            row = (row + [""] * 23)[:23]

        promo_type = (row[1] or "").strip().upper()
        # priority at index 19
        if not row[19] or not is_int(row[19]):
            row[19] = DEFAULT_PRIORITY.get(promo_type, "70")
            changed_priority += 1

        # store_scope at index 7
        normalized, unresolved = normalize_store_scope(row[7], valid_ids, name_to_id)
        if normalized != row[7]:
            row[7] = normalized
            changed_stores += 1
        if unresolved:
            unresolved_notes.append((i, unresolved))

        fixed.append(row)

    # backup & write
    bak = promos_path.with_suffix(".csv.bak")
    promos_path.replace(bak)
    with promos_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(fixed)

    print(f"✔ Wrote normalized promotions to {promos_path}")
    print(f"• Backup saved as {bak}")
    print(f"• Priorities fixed: {changed_priority}")
    print(f"• store_scope normalized: {changed_stores}")
    if unresolved_notes:
        print("• Unresolved store tokens (please correct manually):")
        for line_no, toks in unresolved_notes:
            print(f"  - Line {line_no}: {', '.join(toks)}")

if __name__ == "__main__":
    main()
