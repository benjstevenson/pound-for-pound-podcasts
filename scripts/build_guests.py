"""Phase 2: apply manual overrides to the rule-based extraction and write data/guests.csv.

Inputs:  data/raw/guests_auto.csv (scripts/extract_guests.py), data/guest_overrides.csv (manual review)
Outputs: data/guests.csv          one row per (show, guest), repeat appearances collapsed
         data/guest_episodes.csv  one row per (episode, guest) before de-duping
"""
import csv, re, unicodedata
import pandas as pd

auto = pd.read_csv("data/raw/guests_auto.csv", dtype=str).fillna("")
ov = pd.read_csv("data/guest_overrides.csv", dtype=str, keep_default_na=False)
ov = ov.drop_duplicates("episode_id", keep="last").set_index("episode_id")

# Name normalisation: canonical spellings for people who appear under several variants.
ALIASES = {
    # Phase 4 review: name-parsing artifacts and variants found while grading
    "Brent Beshore Returns": "Brent Beshore", "Craig Mod Returns": "Craig Mod", "Alex Wang": "Alexandr Wang", "Fussman. Cal": "Cal Fussman", "Grasse Tyson": "Neil deGrasse Tyson", "Justin Fishner": "Justin Fishner-Wolfson", "Karen Karniol": "Karen Karniol-Tambour", "Lion Tracker": "Boyd Varty", "Lulu Cheng": "Lulu Cheng Meservey", "Nicholas Taleb": "Nassim Nicholas Taleb", "Pat Dorsey Returns": "Pat Dorsey", "Rich Barton Built Expedia": "Rich Barton",
    "Ed Glaeser": "Edward Glaeser", "Larry White": "Lawrence H. White", "Mike Munger": "Michael Munger",
    "Max Meyer": "Maxwell Meyer", "Rob Slaughter": "Robert Slaughter", "Tibo Sottiaux": "Thibault Sottiaux",
    "Edward Thorp": "Ed Thorp", "Robert Iger": "Bob Iger", "Sam Bankman": "Sam Bankman-Fried",
    "Balaji S. Srinivasan": "Balaji Srinivasan", "Suli Ali": "Suleman Ali", "Gary Vee": "Gary Vaynerchuk",
    "William MacAskill": "Will MacAskill", "Dom D'Agostino": "Dominic D'Agostino", "Dominic D’Agostino": "Dominic D'Agostino",
    "Robert A. Iger": "Bob Iger", "Edward O. Thorp": "Ed Thorp", "Nassim N. Taleb": "Nassim Nicholas Taleb",
    "Jordan B. Peterson": "Jordan Peterson", "Madeleine K. Albright": "Madeleine Albright", "Vivek H. Murthy": "Vivek Murthy",
    "Daniel H. Pink": "Daniel Pink", "John A. List": "John List", "Christopher M. Palmer": "Chris Palmer",
    "Aryeh B. Bourkoff": "Aryeh Bourkoff", "Stephen J. Dubner": "Stephen Dubner", "John F. Crowley": "John Crowley",
    "B.J. Novak": "BJ Novak", "Lloyd Blanfein": "Lloyd Blankfein", "Keller Cliffton": "Keller Rinaudo Cliffton",
    "Willaim Cohan": "William Cohan", "Jessie Zhang": "Jesse Zhang", "Amjad Massad": "Amjad Masad",
    "Dave Baszucki": "David Baszucki", "Ev Randle": "Everett Randle", "Filip Aronshtein": "Fil Aronshtein",
    "Pat Grady": "Pat Grady", "Andy Elliot": "Andy Elliott", "Steven Schwartz": "Steven Schwarz",
    "Jiang Xueqin": "Jiang Xueqin", "Mike Israetel": "Mike Israetel", "Kaitlyn Michelle Siragusa": "Kaitlyn Siragusa",
    "Mati Staniszewski": "Mati Staniszewski", "Rahm Emanuel": "Rahm Emanuel", "Ken Griffin": "Ken Griffin",
    "Arthur De Vany": "Art De Vany",
    # spelling / nickname / middle-initial variants of the same person
    "Antonio Garcia Martinez": "Antonio García Martínez", "Arthur C. Brooks": "Arthur Brooks", "Aviok Kohli": "Avlok Kohli",
    "Bjorn Lomborg": "Bjørn Lomborg", "Clément Delangue": "Clem Delangue", "Cristobal Valenzuela": "Cristóbal Valenzuela",
    "Cynthia L. Haven": "Cynthia Haven", "Dan Pink": "Daniel Pink", "Heinemeier Hansson": "David Heinemeier Hansson",
    "DHH": "David Heinemeier Hansson", "Matt Ball": "Matthew Ball", "Doug Irwin": "Douglas Irwin", "Rick Hanushek": "Eric Hanushek",
    "Francois Chollet": "François Chollet", "Gabe Stengel": "Gabriel Stengel", "Garret Langley": "Garrett Langley",
    "Grant Lafontaine": "Grant LaFontaine", "Gustav Soderstrom": "Gustav Söderström", "Joseph Carlsmith": "Joe Carlsmith",
    "John B. Quinn": "John Quinn", "Joshua Reeves": "Josh Reeves", "Joshua Waitzkin": "Josh Waitzkin", "Ken Rogoff": "Kenneth Rogoff",
    "William Fedus": "Liam Fedus", "Lulu Meservey": "Lulu Cheng Meservey", "Matt Walker": "Matthew Walker",
    "Michael LaFramboise": "Michael Laframboise", "Nicholas Bostrom": "Nick Bostrom", "Patrick Mcgee": "Patrick McGee",
    "Philip E. Tetlock": "Philip Tetlock", "Sarah C. M. Paine": "Sarah Paine", "Simon Hørup Eskildsen": "Simon Eskildsen",
    "Steve Simoni": "Steven Simoni", "Steve Teles": "Steven Teles", "Thomas Mueller": "Tom Mueller", "Tobi Lutke": "Tobi Lütke",
    "Yuval Harari": "Yuval Noah Harari", "Zach Perret": "Zachary Perret", "Ben Horwitz": "Ben Horowitz",
    "Bernt Bornich": "Bernt Børnich", "Cyan Bannister": "Cyan Banister", "Gabor Mate": "Gabor Maté", "Gabor Mat": "Gabor Maté",
    "Joe Wiesenthal": "Joe Weisenthal", "Ryan Peterson": "Ryan Petersen", "Dan Klein": "Daniel Klein",
    "Cliff Winston": "Clifford Winston", "Ahmed Fouad Alkhatib": "Ahmed Alkhatib", "Avi Schiffman": "Avi Schiffmann",
    "Soren Monroe": "Soren Monroe-Anderson", "Edward Mehr": "Ed Mehr", "Sulemain Ali": "Suleman Ali",
}
# Title/topic fragments that slipped through the rules ("" = drop), and fragments that stand for named people.
FIX = {
    # Phase 4 review: fragments that are not people
    "Deep Dive": "", "EDM Cinderella": "", "Deep Basin": "", "Jiu Jitsu": "", "Jonathan GPT Swift": "", "KevKev TimTim TalkTalk": "", "Tyler Looks Back": "",
    "Daniel P": "", "Randy A": "",
    "Arms Race": "", "AWS Outage Aftermath": "", "Browser Race": "", "Cloud Scores Big": "", "Family Life": "", "Many More": "",
    "U.S. Politics": "", "Accelerated Learning": "", "Featuring Freakonomics": "", "Less Hustle": "", "Less Overwhelm": "",
    "More Output": "", "Productivity Tactics": "", "Secret Project": "", "Support Healthcare Workers Now": "",
    "Winklevoss Twins": "Cameron Winklevoss;Tyler Winklevoss", "Pat Gelsinger Joins VC": "Pat Gelsinger",
    "Mark Zuckerberg Interviews Patrick Collison": "Mark Zuckerberg;Patrick Collison",
    "Tim Ferriss Interviews Arnold Schwarzenegger": "Arnold Schwarzenegger", "A Chess Prodigy": "Josh Waitzkin",
    "Attention Right Now": "Kevin Tracey", "Below Zero": "Sue Flood", "Enhanced Mood": "Dominic D'Agostino",
    "Gymnastic Strength Training": "Christopher Sommer", "Hacker Optimizes Online Dating": "Samy Kamkar",
    "Harvard Negotiation Project": "Sheila Heen", "Machine Fame": "Tom Morello", "Money Mustache": "Pete Adeney",
    "Mr. Money Mustache": "Pete Adeney", "Most Popular Exercise Questions": "Pavel Tsatsouline", "Octopus Teacher": "Craig Foster",
    "Riches Philosopher": "Bryan Johnson", "Workaholics Anonymous": "Ryan Holiday",
    "Workweek Case Studies": "Benedict Dohmen;Santiago Nestares", "Workweek Success Stories": "Charlie Houpert",
    "Sorin Capital": "Jim Higgins;Tom Digan",
}

HONORIFIC = re.compile(r"^(?:Dr\.?|Sir|Prof\.?|Professor|Senator|Sen\.|Rep\.|Gov\.?|Governor|General|Gen\.|Admiral|Secretary|"
                       r"President|Ambassador|Baroness|Lord|Dame|Rabbi|Judge(?= Glock)Z|Mr\.|Mrs\.|Ms\.)\s+")
SUFFIX = re.compile(r",?\s+(?:Jr\.?|Sr\.?|II|III|IV|M\.?D\.?|Ph\.?D\.?|MD|PhD)$")

def norm_name(n):
    n = unicodedata.normalize("NFC", re.sub(r"\s+", " ", n)).strip(" .,;:'\"“”‘’")
    n = n.replace("’", "'")
    while HONORIFIC.match(n): n = HONORIFIC.sub("", n)
    n = SUFFIX.sub("", n)
    return ALIASES.get(n, n)

def expand(s):
    out = []
    for x in [x.strip() for x in s.split(";") if x.strip()]:
        x = FIX.get(x, x)
        out += [norm_name(y) for y in x.split(";") if y.strip()]
    return list(dict.fromkeys(out))

def key(n):  # matching key for de-dupe within a show: case/accents/punctuation-insensitive
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", n).strip()

rows = []
for eid, g in auto.groupby("episode_id", sort=False):
    first = g.iloc[0]
    base = {"show": first.show, "episode_id": eid, "date": first.date, "episode_title": first.title, "source": first.source}
    if eid in ov.index:
        o = ov.loc[eid]
        if o.guests.strip().upper() == "NONE":
            rows.append({**base, "guest_name": "", "role": "", "status": "non_guest", "method": "manual", "note": o.note}); continue
        roles = dict(zip(g.guest_name, g.role))
        for n in expand(o.guests):
            rows.append({**base, "guest_name": norm_name(n), "role": roles.get(n, ""), "status": "guest", "method": "manual", "note": o.note})
        continue
    if (g.status == "guest").any():
        names = [n for x in g.guest_name[g.status == "guest"] for n in expand(x)]
        roles = dict(zip(g.guest_name, g.role))
        if not names:
            rows.append({**base, "guest_name": "", "role": "", "status": "non_guest", "method": "fix_dropped", "note": ""})
        for n in dict.fromkeys(names):
            rows.append({**base, "guest_name": n, "role": roles.get(n, ""), "status": "guest", "method": first.method, "note": ""})
    else:
        rows.append({**base, "guest_name": "", "role": "", "status": first.status, "method": first.method, "note": ""})

ge = pd.DataFrame(rows)
ge.to_csv("data/guest_episodes.csv", index=False)

gu = ge[ge.status == "guest"].copy()
gu["k"] = gu.guest_name.map(key)
gu = gu.sort_values("date")
agg = gu.groupby(["show", "k"]).agg(
    guest_name=("guest_name", "first"),
    role=("role", lambda s: next((x for x in s if x), "")),
    appearances=("episode_id", "nunique"),
    first_date=("date", "min"), last_date=("date", "max"),
    episode_ids=("episode_id", lambda s: ";".join(dict.fromkeys(s))),
    episode_titles=("episode_title", lambda s: " || ".join(dict.fromkeys(s))[:300]),
).reset_index().drop(columns="k")
agg.to_csv("data/guests.csv", index=False)

order = pd.read_csv("data/shows.csv").show
ep = ge.groupby(["show", "episode_id"]).status.first().reset_index()
summ = ep.groupby(["show", "status"]).size().unstack(fill_value=0).reindex(order).fillna(0).astype(int)
summ["unique_guests"] = agg.groupby("show").size().reindex(order).fillna(0).astype(int)
print(summ.to_string())
print("total unique (show, guest):", len(agg), "| unique people:", agg.guest_name.map(key).nunique())
