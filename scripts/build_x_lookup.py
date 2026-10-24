"""Phase 3e: data/x_lookup.csv - the guests Ben runs through Grok for X follower counts (Job B).

Only guests who could plausibly make a show's top 50 by Guest Weight:
  - anyone with an English Wikipedia article (Fame can be high), or
  - every guest of a show with <= 150 unique guests (almost anyone could make that show's top 50), or
  - a podcast-stated role that suggests stature 3+ (partner at a fund, professor, president, bestselling author,
    senior government office, a $1B+ company ...), or
  - guests who appeared on 2+ of the shows (a signal of prominence).
x_handle_guess comes from Wikidata (P2002) where we have it; Grok should verify it rather than trust it.
x_handle is blank for Grok to fill (README Part 3 asks it for x_handle, x_followers, x_profile_url).
"""
import re
import pandas as pd

gd = pd.read_csv("data/guest_data.csv").fillna("")
guests = pd.read_csv("data/guests.csv").fillna("")
size = guests.show.value_counts()
small = set(size[size <= 150].index)
# plain "founder/CEO of X" is left out: most such guests are stature 2; the big ones have articles or appear on 2+ shows
ROLE3 = re.compile(r"\b(?:general partner|managing partner|founding partner|partner at|professor|bestsell\w*|best-sell\w*|president|"
                   r"chairman|chairwoman|chair of|senator|secretary of|governor|minister|ambassador|nobel|editor-in-chief|"
                   r"billion|unicorn|\$\d+(?:\.\d+)?\s?(?:b|bn|billion)\b)", re.I)

on_small = set(guests[guests.show.isin(small)].guest_name)
role3 = set(guests[guests.role.str.contains(ROLE3)].guest_name)
rows = []
for _, r in gd.iterrows():
    reasons = []
    if r.wikipedia_article: reasons.append("wikipedia")
    if r.guest_name in on_small: reasons.append("small show")
    if r.guest_name in role3: reasons.append("senior role")
    if int(r.n_shows) >= 2: reasons.append("2+ shows")
    if not reasons: continue
    shows = r.shows.replace("; ", ", ")
    kf = r.known_for or r.wd_description
    if not kf:   # fall back to an episode title so Grok can tell who this is
        t = guests[guests.guest_name == r.guest_name].episode_titles.iloc[0].split(" || ")[0]
        kf = f'guest on "{t[:90]}"'
    handle = r.x_handle_wikidata.split("|")[0]
    rows.append({"guest_name": r.guest_name, "known_for": f"{kf[:150]} (podcasts: {shows})",
                 "x_handle_guess": "@" + handle if handle else "", "x_handle": "", "x_followers": "", "x_profile_url": "",
                 "notes": "", "_why": ", ".join(reasons)})
x = pd.DataFrame(rows).sort_values("guest_name")
x.drop(columns="_why").to_csv("data/x_lookup.csv", index=False)
x[["guest_name", "_why"]].to_csv("data/raw/x_lookup_reasons.csv", index=False)
print(len(x), "guests in x_lookup.csv of", len(gd), "| with a Wikidata handle guess:", (x.x_handle_guess != "").sum())
print(x._why.str.split(", ").explode().value_counts().to_string())
