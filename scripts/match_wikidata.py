"""Phase 3c: pick the right Wikidata person for each guest (or none).

Evidence per candidate, compared against what the podcasts say about the guest (role, episode
titles, opening of each episode description):
  strong  - an organisation the candidate founded or worked for (Wikidata P112/P108), or a
            distinctive proper noun from the candidate's description, appears in the guest context
  field   - the candidate's field (from description + occupations) overlaps the guest's field
A candidate is accepted when it has strong evidence and no rival also has it, or when it is the
only candidate whose field fits and it has an English Wikipedia article. Everything else stays
unmatched (blank fame data) - we never guess.
"""
import json, re
import pandas as pd

cands = json.load(open("data/raw/wikidata/candidates.json"))
guests = pd.read_csv("data/guests.csv").fillna("")
ge = pd.read_csv("data/guest_episodes.csv").fillna("")
eps = pd.read_csv("data/episodes.csv").fillna("").set_index("episode_id")

FIELDS = {
    "business": r"entrepreneur|business|founder|co-?founder|ceo|executive|investor|venture|capitalist|financier|banker|"
                r"hedge fund|private equity|startup|company|chief|president of|chairman|manager|marketer|trader|real estate|"
                r"economist|fund|capital|firm|operator|brand|retail|ecommerce|e-commerce",
    "tech": r"computer|software|engineer|programmer|developer|technolog|internet|artificial intelligence|\bai\b|machine learning|"
            r"robot|hacker|crypto|bitcoin|blockchain|semiconductor|chip|data scien|tech",
    "science": r"scientist|physicist|biologist|chemist|neuroscien|researcher|professor|academic|mathematician|astronom|"
               r"geneticist|psycholog|physician|medical|doctor|surgeon|psychiatrist|biotech|scholar|university",
    "econ_policy": r"economist|econom|political scientist|policy|think tank|historian|philosopher|sociolog|anthropolog|lawyer|"
                   r"jurist|legal scholar|judge",
    "politics": r"politician|senator|congress|representative|governor|mayor|minister|secretary of|diplomat|ambassador|"
                r"president of the united states|vice president|official|government|administrator|white house|cabinet",
    "writing_media": r"writer|author|novelist|poet|journalist|columnist|blogger|essayist|editor|podcast|broadcaster|"
                     r"youtuber|youtube|television presenter|presenter|commentator|reporter|screenwriter|"
                     r"newsletter|content creator|influencer",
    "sports": r"athlete|player|footballer|basketball|baseball|boxer|fighter|mixed martial|ufc|wrestler|olympi|swimmer|runner|"
              r"cyclist|racing driver|surfer|skateboard|coach|chess|poker|tennis|golf|nfl|nba|mma|weightlift|bodybuild",
    "arts": r"actor|actress|musician|singer|rapper|record producer|composer|painter|sculptor|photographer|"
            r"chef|dancer|comedian|filmmaker|film director",
}
FIELD_RE = {k: re.compile(v, re.I) for k, v in FIELDS.items()}
SHOW_FIELDS = {
    "EconTalk": {"econ_policy", "science", "writing_media", "business"}, "Conversations with Tyler": {"econ_policy", "science", "writing_media", "arts"},
    "How I Write": {"writing_media", "arts"}, "Dwarkesh Podcast": {"tech", "science", "econ_policy"},
    "Invest Like the Best": {"business"}, "Lenny's Podcast": {"business", "tech"}, "TBPN": {"business", "tech"},
    "Sourcery": {"business", "tech"}, "Uncapped with Jack Altman": {"business", "tech"}, "No Priors": {"tech", "business", "science"},
    "Relentless": {"business", "tech"}, "Cheeky Pint": {"business", "tech"}, "David Senra": {"business"},
    "My First Million": {"business"}, "All-In": {"business", "tech", "politics"},
}
BIZ_SHOWS = {"TBPN", "Sourcery", "Invest Like the Best", "Lenny's Podcast", "No Priors", "Relentless", "Cheeky Pint",
             "Uncapped with Jack Altman", "David Senra", "Dwarkesh Podcast"}
GENERIC_ORG = {"university", "college", "company", "inc", "group", "the", "google", "apple", "microsoft", "amazon", "facebook", "meta"}

def fields_of(text):
    return {k for k, r in FIELD_RE.items() if r.search(text)}

# context for each guest: role + titles + opening of each description they appear in
ctx, ctx_strict = {}, {}
gi = ge[ge.status == "guest"].groupby("guest_name")
for name, g in gi:
    parts = list(g.role) + list(g.episode_title)
    ctx_strict[name] = " ".join(parts)   # role + titles only: descriptions of multi-guest shows mention other people
    for eid in g.episode_id.unique():
        d = eps.description.get(eid, "")
        i = d.find(name.split()[-1]) if name.split() else -1
        parts.append(d[max(0, i - 200): i + 500] if i >= 0 else d[:500])
    ctx[name] = " ".join(parts)
shows = guests.groupby("guest_name").show.apply(set).to_dict()

def proper_nouns(text):
    return {w for w in re.findall(r"\b[A-Z][A-Za-z0-9&'.-]{2,}(?:\s+[A-Z][A-Za-z0-9&'.-]+)*", text)}

STOP_NOUNS = {"American", "British", "Canadian", "English", "Australian", "German", "French", "Indian", "Chinese", "Israeli",
              "Irish", "Scottish", "Swedish", "Dutch", "Italian", "Spanish", "Japanese", "Korean", "New Zealand", "United States",
              "Professor", "University", "ORCID", "Peerage", "Wikimedia", "Wikipedia", "The"}

rows = []
for name in sorted(shows):
    c = ctx.get(name, "")
    cl = c.lower()
    show_f = set().union(*(SHOW_FIELDS.get(s, set()) for s in shows[name]))
    own_f = fields_of(c)
    # on business/tech shows, a sports or arts candidate must be backed by the guest's own role/titles
    biz_only = shows[name] <= BIZ_SHOWS
    strict_f = fields_of(ctx_strict.get(name, "")) if biz_only else own_f
    ctx_f = own_f if own_f else show_f
    scored = []
    for k in cands.get(name, []):
        text = " ".join([k["desc"], k["occ"].replace("|", " "), k["emp"].replace("|", " "), k["founded"].replace("|", " ")])
        orgs = [o for o in (k["emp"].split("|") + k["founded"].split("|")) if len(o) >= 3 and o.lower() not in GENERIC_ORG]
        org_hit = [o for o in orgs if re.search(r"\b" + re.escape(o.lower()) + r"\b", cl)]
        desc_nouns = {n for n in proper_nouns(k["desc"]) if n not in STOP_NOUNS and len(n) >= 3}
        noun_hit = [n for n in desc_nouns if re.search(r"\b" + re.escape(n.lower()) + r"\b", cl)]
        f = fields_of(text)
        field_hit = bool(f & ctx_f)
        sports_mismatch = (("sports" in f and "sports" not in strict_f) or ("arts" in f and "arts" not in strict_f)
                           or ("politics" in f and "politics" not in ctx_f))
        # candidate fields must overlap on something other than a lone generic field
        if f and f <= {"business"} and not (own_f & {"business"}): field_hit = False
        strong = bool(org_hit or noun_hit)
        scored.append({**k, "org_hit": "|".join(org_hit), "noun_hit": "|".join(noun_hit), "fields": "|".join(sorted(f)),
                       "field_hit": field_hit and not sports_mismatch, "strong": strong})
    strong = [s for s in scored if s["strong"]]
    fit = [s for s in scored if s["field_hit"] and (s["article"] or s["sitelinks"] >= 3)]
    pick, method = None, ""
    if len(strong) == 1:
        pick, method = strong[0], "strong"
    elif len(strong) > 1:
        strong.sort(key=lambda s: -s["sitelinks"])
        if strong[0]["sitelinks"] >= 3 * max(1, strong[1]["sitelinks"]): pick, method = strong[0], "strong+prominence"
    elif len(fit) == 1 and sum(1 for s in scored if s["article"]) <= 1:
        pick, method = fit[0], "field"
    elif len(fit) == 1 and fit[0]["sitelinks"] >= 3 * max([1] + [s["sitelinks"] for s in scored if s is not fit[0] and s["article"]]):
        pick, method = fit[0], "field+prominence"
    elif len(fit) > 1:
        fit.sort(key=lambda s: -s["sitelinks"])
        if fit[0]["sitelinks"] >= 3 * max(1, fit[1]["sitelinks"]) and fit[0]["sitelinks"] >= 10:
            pick, method = fit[0], "field+prominence"
    rows.append({"guest_name": name, "n_candidates": len(scored), "n_with_article": sum(1 for s in scored if s["article"]),
                 "match_method": method, "qid": pick["qid"] if pick else "", "wd_description": pick["desc"] if pick else "",
                 "wikipedia_article": pick["article"] if pick else "", "x_handle_wikidata": pick["x"] if pick else "",
                 "sitelinks": pick["sitelinks"] if pick else "", "evidence": (pick["org_hit"] or pick["noun_hit"] or pick["fields"]) if pick else "",
                 "rejected": " || ".join(f'{s["qid"]}:{s["desc"][:40]}' for s in scored if not pick or s["qid"] != pick["qid"])[:400]})

out = pd.DataFrame(rows)
out.to_csv("data/raw/wikidata/matches.csv", index=False)
print(out.match_method.replace("", "unmatched").value_counts().to_string())
print("matched with enwiki article:", (out.wikipedia_article != "").sum())
