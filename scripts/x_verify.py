"""Verify X handles and fetch follower counts from api.fxtwitter.com (a public mirror of X profile data).

Usage: python3 scripts/x_verify.py <handles.txt>   (one handle per line, with or without @)
Appends one JSON line per handle to data/raw/x/profiles.jsonl (skips handles already fetched).
X_SLEEP sets the pause between requests (default 0.4s). The mirror returns spurious 404s when hit fast, so
delete the 404 lines and re-run with X_SLEEP=3 or more until only genuine misses remain.
"""
import json, os, sys, time, requests

OUT = "data/raw/x/profiles.jsonl"
done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        done.add(json.loads(l)["handle"].lower())
handles = [h.strip().lstrip("@") for h in open(sys.argv[1]) if h.strip()]
todo = [h for h in dict.fromkeys(handles) if h.lower() not in done]
with open(OUT, "a") as f:
    for i, h in enumerate(todo):
        rec = {"handle": h}
        for attempt in range(4):
            try:
                r = requests.get(f"https://api.fxtwitter.com/{h}", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                if r.status_code == 429:
                    time.sleep(30 * (attempt + 1)); continue
                j = r.json()
                u = j.get("user") or {}
                rec.update(status=j.get("code", r.status_code), screen_name=u.get("screen_name"), name=u.get("name"),
                           followers=u.get("followers"), description=(u.get("description") or "")[:300],
                           protected=u.get("protected"), fetched=time.strftime("%Y-%m-%d"))
                break
            except Exception as e:
                rec.update(status="error", error=str(e)[:200]); time.sleep(5)
        f.write(json.dumps(rec) + "\n"); f.flush()
        if i % 50 == 0: print(i, len(todo), flush=True)
        time.sleep(float(os.environ.get("X_SLEEP", "0.4")))
print("done", len(todo))
