"""Dump a compact per-episode review sheet for one show (episodes not already ruled non-guest)."""
import sys, re
import pandas as pd
show, skip_host_only = sys.argv[1], (len(sys.argv) > 2)
g = pd.read_csv("data/raw/guests_auto.csv").fillna("")
e = pd.read_csv("data/episodes.csv", dtype=str).fillna("").set_index("episode_id")
g = g[g.show == show]
for eid, x in g.groupby("episode_id", sort=False):
    st = x.status.iloc[0]
    if st == "non_guest" and (skip_host_only or x.method.iloc[0] != "host_only"): continue
    d = re.sub(r"\(\d+:\d+(?::\d+)?\)\s*", "", e.description[eid])
    names = ";".join(x.guest_name[x.guest_name != ""])
    print(f"{eid} [{st[:3]}:{names}] {e.title[eid][:95]} || {d[:230]}")
