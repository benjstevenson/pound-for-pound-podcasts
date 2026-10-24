"""Job B result -> data/x_followers.csv (one row per guest with a usable X follower count).

Inputs:
  data/x_lookup_filled.csv       Grok's pass over data/x_lookup.csv (handles, follower counts, notes)
  data/x_lookup_extra_filled.csv optional second Grok batch, same format
  data/x_handle_overrides.csv    hand corrections: guest_name, x_handle ("none" = no usable personal account),
                                 x_followers (only used if the live mirror can't see the account), note
  data/raw/x/profiles.jsonl      live profile data fetched by scripts/x_verify.py (api.fxtwitter.com mirror)

Each handle is re-checked against the live profile. The follower count used is the live one. A handle is accepted
only if the live profile exists and its display name or handle contains part of the guest's name (or it's an override).
Rows that fail are kept with status != "ok" and no follower count, so they fall back to Wikipedia fame.
"""
import json, os, re, unicodedata
import pandas as pd

def norm(t):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower())

profiles = {}
for line in open("data/raw/x/profiles.jsonl"):
    p = json.loads(line)
    profiles[p["handle"].lower()] = p

frames = [pd.read_csv("data/x_lookup_filled.csv", dtype=str)]
if os.path.exists("data/x_lookup_extra_filled.csv"):
    frames.append(pd.read_csv("data/x_lookup_extra_filled.csv", dtype=str))
grok = pd.concat(frames).fillna("").drop_duplicates("guest_name", keep="last").set_index("guest_name")
ov = pd.read_csv("data/x_handle_overrides.csv", dtype=str).fillna("").set_index("guest_name")

rows = []
for name, r in grok.iterrows():
    handle = r.x_handle.strip().lstrip("@")
    source = "grok"
    if name in ov.index:
        handle, source = ov.loc[name, "x_handle"].lstrip("@"), "override"
    if not handle or handle.lower() == "none":
        rows.append({"guest_name": name, "x_handle": "", "x_followers": "", "grok_followers": r.x_followers,
                     "status": "none" if handle.lower() == "none" else "not found", "source": source, "x_name": ""})
        continue
    p = profiles.get(handle.lower(), {})
    live = p.get("followers") if p.get("status") == 200 else None
    if live is None and source == "override" and ov.loc[name, "x_followers"]:
        live = int(ov.loc[name, "x_followers"])
    parts = [norm(w) for w in name.split() if len(norm(w)) >= 3]
    name_ok = any(w in norm(p.get("name")) + norm(p.get("screen_name")) for w in parts)
    if live is None:
        status = "no live profile"
    elif source == "override" or name_ok:
        status = "ok"
    else:
        status = "name mismatch"
    rows.append({"guest_name": name, "x_handle": "@" + handle, "x_followers": live if status == "ok" else "",
                 "grok_followers": r.x_followers, "status": status, "source": source, "x_name": p.get("name") or ""})

out = pd.DataFrame(rows).sort_values("guest_name")
out.to_csv("data/x_followers.csv", index=False)
print(out.status.value_counts().to_string())
ok = out[out.status == "ok"].copy()
ok["g"] = pd.to_numeric(ok.grok_followers, errors="coerce")
ok["f"] = pd.to_numeric(ok.x_followers, errors="coerce")
both = ok.dropna(subset=["g", "f"])
print("Grok vs live count within 10%:", ((both.f / both.g).between(0.9, 1.1)).sum(), "of", len(both))
