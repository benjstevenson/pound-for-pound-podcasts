"""Look up candidate RSS feeds for each show via the iTunes Search API."""
import csv, json, time, urllib.parse, requests

UA = {"User-Agent": "Mozilla/5.0 (podcast-p4p research)"}
TERMS = {
    "David Senra": "David Senra",
    "Relentless": "Relentless podcast",
    "Sourcery": "Sourcery Molly O'Shea",
    "Cheeky Pint": "Cheeky Pint Stripe",
}

out = {}
for row in csv.DictReader(open("data/shows.csv")):
    show = row["show"]
    term = TERMS.get(show, show)
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": term, "entity": "podcast", "limit": 8})
    for attempt in range(6):
        r = requests.get(url, headers=UA, timeout=30)
        try:
            res = r.json().get("results", [])
            break
        except ValueError:
            time.sleep(10 * (attempt + 1))
    else:
        print("   FAILED", r.status_code); res = []
    out[show] = [{k: x.get(k) for k in ("collectionName", "artistName", "feedUrl", "trackCount", "collectionId")} for x in res]
    print(f"\n== {show}")
    for x in out[show][:6]:
        print(f"   {x['collectionName']!r:55} | {x['artistName'][:30]:30} | n={x['trackCount']} | {x['feedUrl']}")
    time.sleep(4)
json.dump(out, open("data/raw/itunes_search.json", "w"), indent=1)
