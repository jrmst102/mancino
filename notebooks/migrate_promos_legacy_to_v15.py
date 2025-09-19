#!/usr/bin/env python3
"""
Migrate legacy promotions.csv (promo_id, week_start, week_end, promo_type, scope, sku_ids, mechanic)
to v1.5 canonical schema (23 columns), and emit promotion_items.csv for multi-SKU scopes.

Usage (from repo root):
  python notebooks/migrate_promos_legacy_to_v15.py \
    --in ./data/v1_2025-08-24/promotions.csv \
    --out ./data/v1_2025-08-24/promotions.csv \
    --items-out ./data/v1_2025-08-24/promotion_items.csv

It will back up the legacy file as promotions.legacy.bak.csv before overwriting --out.
"""

from __future__ import annotations
import argparse, csv, re, shutil
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional

V15_HEADER = [
    "promotion_id","promo_type","name","week_start","week_end","scope_type","scope_id","store_scope",
    "amount_off","percent_off","buy_qty","get_qty","new_price","min_qty","min_spend",
    "bundle_type","bundle_qty","bundle_price","limit_per_customer","priority","can_stack","notes","active"
]

ALLOWED_TYPES = {"BOGO","BUNDLE","COUPON","MANAGER_SPECIAL"}

def parse_date(s: str) -> date:
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()

def sunday_on_or_before(d: date) -> date:
    # Monday=0..Sunday=6 → subtract (weekday+1)%7
    return d - timedelta(days=(d.weekday()+1) % 7)

def norm_week(ws: date, we: date) -> Tuple[date,date]:
    ws_norm = sunday_on_or_before(ws)
    return ws_norm, ws_norm + timedelta(days=6)

_dollars = re.compile(r"\$?\s*([0-9]+(?:\.[0-9]{1,2})?)")
_percent = re.compile(r"([0-9]{1,3})\s*%")
_buy_get = re.compile(r"buy\s*(\d+)\s*get\s*(\d+)", re.I)
_bundle = re.compile(r"(\d+)\s*(?:for|x)\s*\$?\s*([0-9]+(?:\.[0-9]{1,2})?)", re.I)
_min_qty = re.compile(r"min(?:imum)?\s*qty\s*(\d+)", re.I)
_min_spend = re.compile(r"min(?:imum)?\s*spend\s*\$?\s*([0-9]+(?:\.[0-9]{1,2})?)", re.I)

def parse_mechanic(ptype: str, mech: str) -> Dict[str,str]:
    """Return dict of v1.5 type-specific fields inferred from free-text mechanic."""
    m = mech.strip()
    out: Dict[str,str] = {}

    if ptype == "BOGO":
        bg = _buy_get.search(m)
        out["buy_qty"] = str(int(bg.group(1))) if bg else "1"
        out["get_qty"] = str(int(bg.group(2))) if bg else "1"

    elif ptype == "COUPON":
        pct = _percent.search(m)
        dol = _dollars.search(m)
        if pct and not dol:
            out["percent_off"] = pct.group(1)
        elif dol and not pct:
            out["amount_off"] = f"{float(dol.group(1)):.2f}"
        else:
            # prefer amount_off if both present; fallback 10% if nothing
            if dol: out["amount_off"] = f"{float(dol.group(1)):.2f}"
            elif pct: out["percent_off"] = pct.group(1)
            else: out["percent_off"] = "10"
        mq = _min_qty.search(m)
        ms = _min_spend.search(m)
        if mq: out["min_qty"] = mq.group(1)
        if ms: out["min_spend"] = f"{float(ms.group(1)):.2f}"

    elif ptype == "MANAGER_SPECIAL":
        # accept either new_price or percent_off
        dol = _dollars.search(m)
        pct = _percent.search(m)
        if dol:
            out["new_price"] = f"{float(dol.group(1)):.2f}"
        elif pct:
            out["percent_off"] = pct.group(1)
        else:
            out["percent_off"] = "15"

    elif ptype == "BUNDLE":
        bb = _bundle.search(m)
        if bb:
            out["bundle_type"] = "mix_n_match"
            out["bundle_qty"] = str(int(bb.group(1)))
            out["bundle_price"] = f"{float(bb.group(2)):.2f}"
        else:
            # default safe bundle: 2 for $6.00
            out["bundle_type"] = "mix_n_match"
            out["bundle_qty"] = "2"
            out["bundle_price"] = "6.00"

    return out

def priority_for(ptype: str) -> str:
    return {"BUNDLE":"90","BOGO":"80","COUPON":"70","MANAGER_SPECIAL":"60"}[ptype]

def can_stack_for(ptype: str) -> str:
    return "TRUE" if ptype in ("COUPON","MANAGER_SPECIAL") else "FALSE"

def build_name(ptype: str, fields: Dict[str,str]) -> str:
    if ptype == "BOGO":
        return f"Buy {fields.get('buy_qty','1')} Get {fields.get('get_qty','1')}"
    if ptype == "COUPON":
        if "amount_off" in fields: return f"${fields['amount_off']} Off (coupon)"
        if "percent_off" in fields: return f"{fields['percent_off']}% Off (coupon)"
        return "Coupon"
    if ptype == "MANAGER_SPECIAL":
        if "new_price" in fields: return f"Manager Special ${fields['new_price']}"
        if "percent_off" in fields: return f"Manager Special {fields['percent_off']}% Off"
        return "Manager Special"
    if ptype == "BUNDLE":
        return f"{fields.get('bundle_qty','2')} for ${fields.get('bundle_price','6.00')}"
    return ptype

def migrate_row(rec: Dict[str,str]) -> Tuple[List[str], List[Tuple[str,str]]]:
    """
    Returns (v15_row, promo_items_pairs)
    where promo_items_pairs is list of (promotion_id, sku_id)
    """
    promo_id = rec.get("promo_id","").strip() or rec.get("promotion_id","").strip()
    week_start = parse_date(rec["week_start"])
    week_end   = parse_date(rec["week_end"])
    ws, we = norm_week(week_start, week_end)

    ptype = rec["promo_type"].strip().upper()
    if ptype not in ALLOWED_TYPES:
        # best effort: map some aliases
        alias = {"MS":"MANAGER_SPECIAL","SPECIAL":"MANAGER_SPECIAL","COUPON":"COUPON","BUNDLE":"BUNDLE","BOGO":"BOGO"}
        ptype = alias.get(ptype, ptype)

    scope_raw = rec.get("scope","").strip().lower()
    sku_ids_raw = rec.get("sku_ids","").strip()
    mechanic = rec.get("mechanic","").strip()

    # scope mapping
    scope_type = "category" if scope_raw.startswith("cat") or scope_raw.startswith("category") else "sku"
    sku_list: List[str] = []
    if scope_type == "sku" and sku_ids_raw:
        # split by comma or semicolon
        sku_list = [s.strip() for s in re.split(r"[;,]", sku_ids_raw) if s.strip()]
    scope_id = (sku_list[0] if sku_list else rec.get("scope_id","").strip()) or "UNKNOWN"

    # infer type-specific fields from mechanic
    fields = parse_mechanic(ptype, mechanic)

    # assemble v1.5 row
    name = build_name(ptype, fields)
    row = [
        promo_id, ptype, name, ws.isoformat(), we.isoformat(),
        scope_type, scope_id, "ALL",
        fields.get("amount_off",""),
        fields.get("percent_off",""),
        fields.get("buy_qty",""),
        fields.get("get_qty",""),
        fields.get("new_price",""),
        fields.get("min_qty",""),
        fields.get("min_spend",""),
        fields.get("bundle_type",""),
        fields.get("bundle_qty",""),
        fields.get("bundle_price",""),
        "6",                        # limit_per_customer default
        priority_for(ptype),        # priority
        can_stack_for(ptype),       # can_stack
        f"migrated:{mechanic.replace(',', ';')}",  # notes (no commas)
        "TRUE"                      # active
    ]
    assert len(row) == len(V15_HEADER)

    # promotion_items for multi-SKU scopes (if any)
    promo_items: List[Tuple[str,str]] = []
    if scope_type == "sku" and len(sku_list) > 1:
        for s in sku_list:
            promo_items.append((promo_id, s))

    return row, promo_items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="legacy promotions.csv")
    ap.add_argument("--out", dest="outp", required=True, help="v1.5 promotions.csv (will overwrite, with backup)")
    ap.add_argument("--items-out", dest="items_out", required=True, help="v1.5 promotion_items.csv (create or append)")
    args = ap.parse_args()

    inp = Path(args.inp)
    outp = Path(args.outp)
    items_out = Path(args.items_out)

    if not inp.exists():
        raise SystemExit(f"[ERROR] {inp} not found")

    # Read legacy rows
    with inp.open(newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        legacy_header = rdr.fieldnames or []
        expected_legacy = {"promo_id","week_start","week_end","promo_type","scope","sku_ids","mechanic"}
        if not set(expected_legacy).issubset(set(legacy_header)):
            raise SystemExit(f"[ERROR] Legacy header not recognized. Found: {legacy_header}")
        legacy_rows = list(rdr)

    # Convert
    v15_rows: List[List[str]] = []
    item_pairs: List[Tuple[str,str]] = []
    for i, rec in enumerate(legacy_rows, start=2):
        try:
            row, pairs = migrate_row(rec)
            v15_rows.append(row)
            item_pairs.extend(pairs)
        except Exception as e:
            raise SystemExit(f"[ERROR] line {i}: {e}")

    # Backup and write promotions.csv
    if outp.exists():
        bak = outp.with_suffix(".legacy.bak.csv")
        shutil.copy2(outp, bak)
        print(f"Backed up existing {outp} to {bak}")

    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(V15_HEADER)
        w.writerows(v15_rows)

    # Write/append promotion_items.csv
    header_items = ["promotion_id","sku_id"]
    write_header = not items_out.exists()
    with items_out.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header_items)
        for pid, sku in item_pairs:
            w.writerow([pid, sku])

    print(f"✔ Migrated {len(v15_rows)} promotions to {outp}")
    if item_pairs:
        print(f"✔ Wrote {len(item_pairs)} promotion_items to {items_out}")
    else:
        print("• No multi-SKU scopes detected (promotion_items not needed)")

if __name__ == "__main__":
    main()
