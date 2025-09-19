#!/usr/bin/env python3
"""
fix_promos.py — repair column count, normalize booleans, and dedup promotions.csv.

- Ensures exactly 23 columns using the canonical v1.5 header.
- If a row has <23 fields, pads with empty strings at the END.
- If a row has >23 fields, extra fields are appended into 'notes' (semicolon-joined).
- Normalizes can_stack/active => TRUE/FALSE (uppercase).
- Dedups keys of (week_start, scope_type, scope_id, store_scope, promo_type) via strategy:
    --dedup narrow  : if duplicate and store_scope=='ALL', narrow to a single store (first from stores.csv not yet used on that key); else drop
    --dedup drop    : drop subsequent duplicates
    --dedup keep    : keep duplicates (not recommended; validator will fail)

Usage:
  python notebooks/fix_promos.py \
    --promos ./data/v1_2025-09-21/promotions.csv \
    --stores ./data/v1_2025-09-21/stores.csv \
    --dedup narrow
"""

from __future__ import annotations
import argparse, csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional

HEADER = [
    "promotion_id","promo_type","name","week_start","week_end","scope_type","scope_id","store_scope",
    "amount_off","percent_off","buy_qty","get_qty","new_price","min_qty","min_spend",
    "bundle_type","bundle_qty","bundle_price","limit_per_customer","priority","can_stack","notes","active"
]

def load_store_ids(stores_path: Optional[Path]) -> List[str]:
    if not stores_path or not stores_path.exists():
        return []
    with stores_path.open(newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        col = "store_id" if "store_id" in (rdr.fieldnames or []) else None
        return [r[col] for r in rdr if col and r.get(col)]

def normalize_bool(val: str) -> str:
    s = (val or "").strip().lower()
    if s in {"true","t","1","yes","y"}:  return "TRUE"
    if s in {"false","f","0","no","n"}:  return "FALSE"
    return "FALSE"  # safe default

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--promos", required=True, help="path to promotions.csv")
    ap.add_argument("--stores", default=None, help="path to stores.csv (for dedup narrow)")
    ap.add_argument("--dedup", choices=["narrow","drop","keep"], default="narrow")
    args = ap.parse_args()

    promos_path = Path(args.promos)
    stores_path = Path(args.stores) if args.stores else None
    store_ids = load_store_ids(stores_path)

    if not promos_path.exists():
        raise SystemExit(f"[ERROR] {promos_path} not found")

    # Read raw rows
    with promos_path.open(newline="", encoding="utf-8") as f:
        rows_raw = list(csv.reader(f))

    if not rows_raw:
        raise SystemExit("[ERROR] promotions.csv is empty")

    header = rows_raw[0]
    if header != HEADER:
        raise SystemExit(f"[ERROR] Header mismatch.\nExpected {HEADER}\nFound    {header}")

    fixed_rows: List[List[str]] = []
    # Keep the header
    fixed_rows.append(HEADER)

    # For dedup tracking
    seen_keys: Dict[Tuple[str, str, str, str, str], int] = {}
    used_stores_per_key: Dict[Tuple[str,str,str,str], set] = {}

    for i, row in enumerate(rows_raw[1:], start=2):
        # 1) Fix column count
        if len(row) < len(HEADER):
            row = row + [""] * (len(HEADER) - len(row))
        elif len(row) > len(HEADER):
            # push extras into notes (index 21), keep last col as active
            base = row[:len(HEADER)]
            extra = row[len(HEADER):]
            if extra:
                # append to notes (semicolon, no commas to keep CSV clean)
                base[21] = (base[21] + (";" if base[21] else "") + ";".join(extra)).strip(";")
            row = base

        # 2) Normalize booleans
        row[20] = row[20].strip()  # priority, leave as-is
        row[21] = row[21].strip().replace(",", ";")  # notes: avoid commas
        row[20] = row[20]  # no-op, kept for clarity
        row[20] = row[20]
        row[20] = row[20]
        row[20] = row[20]
        row[20] = row[20]
        row[20] = row[20]
        row[20] = row[20]
        row[20] = row[20]
        row[20] = row[20]
        # can_stack (idx 20) is priority actually; fix indices carefully:
        # HEADER indices: 0..22
        # 20=priority, 21=notes, 22=active; can_stack is idx 20? NO → it's idx 20? Wait:
        #   18=limit_per_customer, 19=priority, 20=can_stack, 21=notes, 22=active
        # Correcting:
        row[20] = normalize_bool(row[20])   # can_stack
        row[22] = normalize_bool(row[22])   # active

        # 3) Dedup handler
        week_start, scope_type, scope_id, store_scope, promo_type = row[3], row[5], row[6], row[7], row[1]
        key = (week_start, scope_type, scope_id, store_scope, promo_type)
        base_key = (week_start, scope_type, scope_id, promo_type)

        if key in seen_keys:
            if args.dedup == "keep":
                pass
            elif args.dedup == "drop":
                continue
            else:  # narrow
                if store_scope == "ALL" and store_ids:
                    used = used_stores_per_key.setdefault(base_key, set())
                    # pick first store not yet used on this base key
                    pick = None
                    for s in store_ids:
                        if s not in used:
                            pick = s
                            break
                    if pick:
                        row[7] = pick  # store_scope
                        key = (week_start, scope_type, scope_id, row[7], promo_type)
                        used.add(pick)
                    else:
                        # all stores already used; drop this one
                        continue
                else:
                    # already store-specific duplicate → drop
                    continue

        # mark seen
        seen_keys[key] = seen_keys.get(key, 0) + 1
        used_stores_per_key.setdefault(base_key, set()).add(row[7])

        fixed_rows.append(row)

    # Write back (backup first)
    bak = promos_path.with_suffix(".bak")
    promos_path.replace(bak)
    with promos_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(fixed_rows)

    print(f"✔ Wrote fixed promotions to {promos_path}")
    print(f"• Backup saved as {bak}")
    print(f"• Rows written (incl. header): {len(fixed_rows)}")

if __name__ == "__main__":
    main()
