"""Fetch description, English Wikipedia article and X handle for the hand-checked QIDs in manual_matches.csv."""
import json, requests
import pandas as pd

UA = {"User-Agent": "podcast-p4p/0.1 (https://github.com/benjstevenson/podcast-p4p; research script)",
      "Accept": "application/sparql-results+json"}
Q = """SELECT ?item ?desc ?article (GROUP_CONCAT(DISTINCT ?x; separator="|") AS ?xs) WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item schema:description ?desc FILTER(lang(?desc) = "en") }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL { ?item wdt:P2002 ?x }
} GROUP BY ?item ?desc ?article"""
qids = sorted({q for q in pd.read_csv("data/wikidata_manual_matches.csv").qid if q.startswith("Q")})
out = {}
for i in range(0, len(qids), 100):
    r = requests.post("https://query.wikidata.org/sparql", data={"query": Q % " ".join("wd:" + q for q in qids[i:i + 100])},
                      headers=UA, timeout=120)
    r.raise_for_status()
    for b in r.json()["results"]["bindings"]:
        q = b["item"]["value"].rsplit("/", 1)[1]
        out[q] = {"desc": b.get("desc", {}).get("value", ""), "article": b.get("article", {}).get("value", ""),
                  "x": b.get("xs", {}).get("value", "")}
missing = [q for q in qids if q not in out]
json.dump(out, open("data/raw/wikidata/manual_details.json", "w"), indent=0)
print(len(out), "QIDs fetched; missing:", missing, "| with article:", sum(1 for v in out.values() if v["article"]))
