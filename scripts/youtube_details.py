"""Phase 1: fetch upload date + description for unmatched long YouTube videos."""
import json, subprocess
import pandas as pd

df = pd.read_csv("data/raw/youtube_vs_rss.csv").fillna("")
todo = df[(df.duration_min >= 15) & ~df.matched]
out = {}
try:
    out = json.load(open("data/raw/youtube_details.json"))
except FileNotFoundError:
    pass
for _, r in todo.iterrows():
    if r.yt_id in out: continue
    p = subprocess.run(["yt-dlp", "--skip-download", "--no-warnings", "--print",
                        "%(upload_date)s\t%(description)j", f"https://www.youtube.com/watch?v={r.yt_id}"],
                       capture_output=True, text=True, timeout=120)
    line = p.stdout.strip().split("\t", 1)
    out[r.yt_id] = {"upload_date": line[0] if line else "",
                    "description": json.loads(line[1]) if len(line) > 1 else ""}
    json.dump(out, open("data/raw/youtube_details.json", "w"))
print("fetched", len(out))
