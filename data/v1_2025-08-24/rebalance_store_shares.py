#!/usr/bin/env python3
"""
Rebalance store revenues to match target shares by adding (bootstrapping) and dropping transactions.

Inputs (default):
  - transactions.csv
  - transaction_line_items.csv

Outputs:
  - transactions_rebalanced.csv
  - transaction_line_items_rebalanced.csv

Usage examples:
  # Random assignment of [0.35,0.23,0.18,0.14,0.10] across the 5 stores in the data
  python rebalance_store_shares.py

  # Explicit mapping (comma-separated pairs store:share)
  python rebalance_store_shares.py --shares "S0005:0.35,S0003:0.23,S0002:0.18,S0004:0.14,S0001:0.10"

Notes:
  - Keeps overall chain revenue approximately constant.
  - Adds transactions to under-target stores by resampling *within that store*.
  - Drops transactions from over-target stores at random until the gap is closed.
  - Preserves prices/promotions/line items; new transactions get new IDs and slight timestamp jitter.
  - Deterministic with --seed (default 42).
"""
import argparse
import math
import random
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

def parse_share_map(s: str, stores: List[str]) -> Dict[str, float]:
    pairs = [p.strip() for p in s.split(",") if p.strip()]
    out = {}
    for p in pairs:
        k, v = p.split(":")
        out[k.strip()] = float(v.strip())
    # basic checks
    keys = set(out.keys())
    if not keys.issubset(set(stores)):
        missing = keys - set(stores)
        raise ValueError(f"Unknown store keys in --shares: {missing}")
    total = sum(out.values())
    if not (0.999 <= total <= 1.001):
        raise ValueError(f"Shares must sum to 1. Got {total}")
    return out

def random_share_map(stores: List[str], seed=42) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    base = np.array([0.35, 0.23, 0.18, 0.14, 0.10])
    perm = rng.permutation(len(base))
    shares = base[perm]
    return {s: float(shares[i]) for i, s in enumerate(stores)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tx", default="transactions.csv")
    parser.add_argument("--li", default="transaction_line_items.csv")
    parser.add_argument("--out_tx", default="transactions_rebalanced.csv")
    parser.add_argument("--out_li", default="transaction_line_items_rebalanced.csv")
    parser.add_argument("--shares", default=None, help="Explicit mapping like 'S0005:0.35,S0003:0.23,...' (must sum to 1)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    random.seed(args.seed)

    tx_path = Path(args.tx)
    li_path = Path(args.li)
    if not tx_path.exists() or not li_path.exists():
        raise SystemExit(f"Missing required files. Looked for {tx_path} and {li_path}")

    tx = pd.read_csv(tx_path, parse_dates=["txn_ts"])
    li = pd.read_csv(li_path)

    # compute current revenue per store
    rev_by_tx = li.groupby("transaction_id", as_index=False)["line_total"].sum().rename(columns={"line_total":"tx_total_li"})
    tx = tx.merge(rev_by_tx, on="transaction_id", how="left")
    # prefer recomputed line-item total to avoid divergence
    tx["total"] = tx["tx_total_li"].fillna(tx["total"])
    store_rev = tx.groupby("store_id")["total"].sum().sort_values(ascending=False)
    stores = list(store_rev.index)
    chain_total = float(store_rev.sum())

    # target shares
    if args.shares:
        share_map = parse_share_map(args.shares, stores)
    else:
        share_map = random_share_map(stores, seed=args.seed)

    target_rev = {s: chain_total * share_map[s] for s in stores}

    # split stores into needs_add / needs_drop
    diffs = {s: target_rev[s] - float(store_rev[s]) for s in stores}
    needs_add = [s for s in stores if diffs[s] > 0]
    needs_drop = [s for s in stores if diffs[s] < 0]

    # helpers for sampling transactions by store
    tx_by_store = {s: tx[tx["store_id"] == s].copy() for s in stores}
    li_by_tx = {tid: g.copy() for tid, g in li.groupby("transaction_id")}

    # we'll build new tx/li lists
    tx_keep = []       # transactions to keep (original or not dropped)
    li_keep = []

    # --- DROP pass ---
    to_drop_ids = set()
    for s in needs_drop:
        surplus = -diffs[s]
        # randomize order
        candidates = tx_by_store[s].sample(frac=1.0, random_state=random.randint(0,10**9))
        removed = 0.0
        for _, row in candidates.iterrows():
            if removed >= surplus:
                break
            to_drop_ids.add(row["transaction_id"])
            removed += float(row["total"])
        # keep the rest
        keep_ids = candidates[~candidates["transaction_id"].isin(to_drop_ids)]["transaction_id"].tolist()
        tx_keep.append(candidates[candidates["transaction_id"].isin(keep_ids)])
        for tid in keep_ids:
            if tid in li_by_tx:
                li_keep.append(li_by_tx[tid])

    # stores that don't need drops: keep all initially
    for s in stores:
        if s not in needs_drop:
            tdf = tx_by_store[s]
            tx_keep.append(tdf)
            for tid in tdf["transaction_id"]:
                if tid in li_by_tx:
                    li_keep.append(li_by_tx[tid])

    tx_kept = pd.concat(tx_keep, ignore_index=True)

    # --- ADD pass ---
    # find max txn id to create new unique ids
    def parse_num(tid):
        # expects like T0000123
        try:
            return int(tid[1:])
        except Exception:
            return None

    max_num = max([parse_num(t) for t in tx["transaction_id"] if parse_num(t) is not None] + [0])
    next_num = max_num + 1

    new_tx_rows = []
    new_li_rows = []

    for s in needs_add:
        deficit = diffs[s]
        pool = tx_by_store[s].copy()
        if pool.empty or deficit <= 0:
            continue
        # sample with replacement until we close the gap
        added = 0.0
        # shuffle pool order for variety
        pool = pool.sample(frac=1.0, random_state=random.randint(0,10**9))
        idx = 0
        while added < deficit and len(pool) > 0:
            row = pool.iloc[idx % len(pool)]
            idx += 1
            old_tid = row["transaction_id"]
            new_tid = f"T{str(next_num).zfill(7)}"
            next_num += 1

            # jitter timestamp by 0-59 minutes
            jitter_minutes = int(rng.integers(0, 60))
            new_ts = row["txn_ts"] + pd.Timedelta(minutes=jitter_minutes)

            # copy tx row
            new_row = row.copy()
            new_row["transaction_id"] = new_tid
            new_row["txn_ts"] = new_ts

            # copy line items and recompute totals to avoid drift
            if old_tid in li_by_tx:
                li_rows = li_by_tx[old_tid].copy()
                li_rows["transaction_id"] = new_tid
                # tiny noise to line_total within +/- 1% but cap at line_subtotal
                noise = rng.uniform(0.99, 1.01)
                li_rows["line_total"] = (li_rows["line_total"] * noise).clip(upper=li_rows["line_subtotal"]).round(2)
                li_rows["line_discount"] = (li_rows["line_subtotal"] - li_rows["line_total"]).round(2)
                # recompute tx totals
                totals = li_rows[["line_subtotal","line_discount","line_total"]].sum()
                new_row["subtotal"] = round(float(totals["line_subtotal"]), 2)
                new_row["discount_total"] = round(float(totals["line_discount"]), 2)
                # tax approx again (8.875% * 80% taxable base)
                new_row["tax"] = round(0.08875 * 0.8 * new_row["subtotal"], 2)
                new_row["total"] = round(float(totals["line_total"]) + new_row["tax"], 2)
                new_tx_rows.append(new_row)
                new_li_rows.append(li_rows)
                added += float(new_row["total"])
            else:
                # if no line items strangely, skip
                continue

    tx_final = pd.concat([tx_kept, pd.DataFrame(new_tx_rows)], ignore_index=True)
    li_final = pd.concat(li_keep + new_li_rows, ignore_index=True)

    # Final QA: compute shares
    final_rev = tx_final.groupby("store_id")["total"].sum()
    final_share = (final_rev / final_rev.sum()).sort_values(ascending=False)

    # Save
    tx_final.sort_values("txn_ts").to_csv(args.out_tx, index=False)
    li_final.to_csv(args.out_li, index=False)

    print("Target shares:", {k: round(v, 4) for k, v in share_map.items()})
    print("Final shares: ", {k: round(float(final_share[k]), 4) for k in final_share.index})
    print("Wrote:", args.out_tx, "and", args.out_li)

if __name__ == "__main__":
    main()
