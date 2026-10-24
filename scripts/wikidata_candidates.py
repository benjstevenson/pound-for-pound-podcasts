"""Phase 3a: pull every Wikidata human whose English label or alias exactly matches a guest name.

Uses the Wikidata Query Service (SPARQL); the regular Wikidata/Wikipedia APIs rate-limit this
server's shared IP. Writes data/raw/wikidata/candidates.json: {guest_name: [candidate, ...]}.
"""
import json, os, time, requests
import pandas as pd

UA = {"User-Agent": "podcast-p4p/0.1 (https://github.com/benjstevenson/podcast-p4p; research script)",
      "Accept": "application/sparql-results+json"}
OUT = "data/raw/wikidata/candidates.json"

def lit(s):
    # match English labels and the language-neutral "mul" labels Wikidata now uses for many people
    e = '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return e + "@en " + e + "@mul"

Q = """SELECT ?name ?item ?desc ?sl ?article ?x
  (GROUP_CONCAT(DISTINCT ?occL; separator="|") AS ?occ)
  (GROUP_CONCAT(DISTINCT ?empL; separator="|") AS ?emp)
  (GROUP_CONCAT(DISTINCT ?fndL; separator="|") AS ?founded)
  (SAMPLE(?birth) AS ?born) WHERE {
  VALUES ?lab { %s }
  ?item rdfs:label|skos:altLabel ?lab .
  BIND(STR(?lab) AS ?name)
  ?item wdt:P31 wd:Q5 ; wikibase:sitelinks ?sl .
  OPTIONAL { ?item schema:description ?desc FILTER(lang(?desc) = "en") }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL { ?item wdt:P2002 ?x }
  OPTIONAL { ?item wdt:P569 ?birth }
  OPTIONAL { ?item wdt:P106 ?o . ?o rdfs:label ?occL FILTER(lang(?occL) = "en") }
  OPTIONAL { ?item wdt:P108 ?e . ?e rdfs:label ?empL FILTER(lang(?empL) = "en") }
  OPTIONAL { ?f wdt:P112 ?item . ?f rdfs:label ?fndL FILTER(lang(?fndL) = "en") }
} GROUP BY ?name ?item ?desc ?sl ?article ?x"""

names = sorted(set(pd.read_csv("data/guests.csv").guest_name.dropna()))
out = json.load(open(OUT)) if os.path.exists(OUT) else {}
todo = [n for n in names if n not in out]
B = 40
for i in range(0, len(todo), B):
    batch = todo[i:i + B]
    for attempt in range(5):
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": Q % " ".join(map(lit, batch))},
                              headers=UA, timeout=120)
            if r.status_code == 200: break
            time.sleep(20 * (attempt + 1))
        except requests.RequestException:
            time.sleep(20 * (attempt + 1))
    else:
        print("FAILED batch", i, r.status_code); continue
    for n in batch: out.setdefault(n, [])
    for b in r.json()["results"]["bindings"]:
        v = {k: x["value"] for k, x in b.items()}
        c = {"qid": v["item"].rsplit("/", 1)[1], "desc": v.get("desc", ""), "sitelinks": int(v.get("sl", 0)),
             "article": v.get("article", ""), "x": v.get("x", ""), "occ": v.get("occ", ""), "emp": v.get("emp", ""),
             "founded": v.get("founded", ""), "born": v.get("born", "")[:10]}
        lst = out.setdefault(v["name"], [])
        old = next((o for o in lst if o["qid"] == c["qid"]), None)
        if old:   # several X handles -> keep them all
            if c["x"] and c["x"] not in old["x"].split("|"): old["x"] = "|".join(filter(None, [old["x"], c["x"]]))
        else:
            lst.append(c)
    json.dump(out, open(OUT, "w"))
    print(f"{i + len(batch)}/{len(todo)}", flush=True)
    time.sleep(1)
print("names with >=1 human candidate:", sum(1 for v in out.values() if v), "of", len(out))
