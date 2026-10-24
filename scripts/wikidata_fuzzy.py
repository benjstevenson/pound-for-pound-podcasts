"""Phase 3b-2: fuzzy Wikidata search (EntitySearch via WDQS) for guests still unmatched after exact-label matching.

Catches people whose Wikidata label differs from the podcast name (middle initials, "Jr.", nicknames).
Results are only suggestions: they go to data/raw/wikidata/review_fuzzy.txt for manual review.
"""
import json, os, time, requests
import pandas as pd

UA = {"User-Agent": "podcast-p4p/0.1 (https://github.com/benjstevenson/podcast-p4p; research script)",
      "Accept": "application/sparql-results+json"}
OUT = "data/raw/wikidata/fuzzy.json"
Q = """SELECT ?name ?item ?label ?desc ?sl ?article WHERE {
 VALUES ?name { %s }
 SERVICE wikibase:mwapi { bd:serviceParam wikibase:api "EntitySearch"; wikibase:endpoint "www.wikidata.org";
   mwapi:search ?name; mwapi:language "en". ?item wikibase:apiOutputItem mwapi:item. }
 ?item wdt:P31 wd:Q5; wikibase:sitelinks ?sl.
 OPTIONAL { ?item rdfs:label ?label FILTER(lang(?label) IN ("en", "mul")) }
 OPTIONAL { ?item schema:description ?desc FILTER(lang(?desc) = "en") }
 OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
}"""
m = pd.read_csv("data/raw/wikidata/matches.csv").fillna("")
manual = set(pd.read_csv("data/wikidata_manual_matches.csv").guest_name)
names = [n for n in m[m.qid == ""].guest_name if n not in manual]
out = json.load(open(OUT)) if os.path.exists(OUT) else {}
todo = [n for n in names if n not in out]
B = 20
for i in range(0, len(todo), B):
    batch = todo[i:i + B]
    vals = " ".join('"' + n.replace("\\", "\\\\").replace('"', '\\"') + '"' for n in batch)
    for attempt in range(5):
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": Q % vals}, headers=UA, timeout=120)
            if r.status_code == 200: break
        except requests.RequestException:
            pass
        time.sleep(20 * (attempt + 1))
    else:
        print("FAILED batch", i); continue
    for n in batch: out.setdefault(n, [])
    for b in r.json()["results"]["bindings"]:
        v = {k: x["value"] for k, x in b.items()}
        lst = out[v["name"]]
        q = v["item"].rsplit("/", 1)[1]
        if not any(c["qid"] == q for c in lst):
            lst.append({"qid": q, "label": v.get("label", ""), "desc": v.get("desc", ""), "sitelinks": int(v["sl"]),
                        "article": v.get("article", "")})
    json.dump(out, open(OUT, "w"))
    print(f"{i + len(batch)}/{len(todo)}", flush=True)
    time.sleep(1)
