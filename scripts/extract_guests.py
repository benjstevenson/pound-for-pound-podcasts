"""Phase 2: rule-based guest extraction from episode titles/descriptions.

Writes data/raw/guests_auto.csv: one row per (episode, guest candidate), plus one row per
episode with no guest found (guest_name blank) and a `status` column:
  guest      - guest found by a rule
  non_guest  - episode classified as solo/host-only/clip/trailer/rerun/best-of/Q&A/compilation
  unresolved - no rule fired; needs manual review
"""
import re
import pandas as pd
import gender_guesser.detector as gender

FIRST = gender.Detector(case_sensitive=False)
def known_first(tok):
    return FIRST.get_gender(tok.strip(".'’")) != "unknown"

eps = pd.read_csv("data/episodes.csv", dtype=str).fillna("")
for c in ("title", "description"):   # zero-width characters break the link/name patterns
    eps[c] = eps[c].str.replace(r"[\u2060\u200b\u200c\u200d\ufeff\u00a0]", " ", regex=True)

# Ordinary English words: tokens that appear in lowercase often across all descriptions.
from collections import Counter
_lc = Counter(w for d in eps.description for w in re.findall(r"(?<![A-Za-z])[a-z]{3,}(?![A-Za-z])", d))
COMMON = {w for w, c in _lc.items() if c >= 8}

def plausible_person(n):
    toks = n.split()
    if known_first(toks[0]): return True
    return not any(t.lower().strip(".'’") in COMMON for t in toks)

DASH = r"\s*[–—-]\s*"
HOSTS = {
    "David Senra": ["David Senra"], "How I Write": ["David Perell"], "Dwarkesh Podcast": ["Dwarkesh Patel"],
    "Relentless": ["Ti Morse"], "Cheeky Pint": ["John Collison"], "Conversations with Tyler": ["Tyler Cowen"],
    "EconTalk": ["Russ Roberts"], "No Priors": ["Sarah Guo", "Elad Gil"], "Uncapped with Jack Altman": ["Jack Altman"],
    "Sourcery": ["Molly O'Shea", "Molly O’Shea"], "Invest Like the Best": ["Patrick O'Shaughnessy", "Patrick O’Shaughnessy"],
    "The Knowledge Project": ["Shane Parrish"], "Lenny's Podcast": ["Lenny Rachitsky"], "Jack Neel Podcast": ["Jack Neel"],
    "Lex Fridman Podcast": ["Lex Fridman"],
    "All-In": ["Chamath Palihapitiya", "Jason Calacanis", "David Sacks", "David Friedberg", "Chamath", "Jason", "Sacks", "Friedberg"],
    "The Tim Ferriss Show": ["Tim Ferriss"], "TBPN": ["John Coogan", "Jordi Hays"],
    "My First Million": ["Sam Parr", "Shaan Puri", "Sam", "Shaan"],
}

NON_GUEST = re.compile(
    r"\btrailer\b|\bbest of\b|\breplay\b|\brerun\b|\bre-?release\b|\bencore\b|\bclassic episode\b|"
    r"\bq\s?&\s?a\b|\bama\b|ask me anything|\bmailbag\b|\brecap\b|\bhighlights\b|\bcompilation\b|"
    r"in case you missed it|\bdiet tbpn\b|the random show|tim ferriss show classics|\bbook excerpt\b|"
    r"\[outliers\]|\boutliers:|\binbetweenisode\b|\bbonus:|\bannouncement\b|coming soon|welcome to|"
    r"\bpreview\b|\bsneak peek\b|year in review|\bsolo\b|\bclip\b|\bteaser\b", re.I)

NAME_TOKEN = r"(?:[A-Z][\w'’.\-]*|de|da|van|von|der|del|la|le|bin|al|al-|du|di|dos|ten|of)"
NAME_RE = re.compile(rf"^(?:Dr\.?\s+|Sir\s+|Prof\.?\s+|Professor\s+|General\s+|Gen\.\s+|Admiral\s+|Senator\s+|Gov\.?\s+|Governor\s+|Rabbi\s+|Rep\.\s+)?"
                     rf"[A-Z][\w'’.\-]*(?:\s+{NAME_TOKEN}){{1,4}}(?:,?\s+(?:Jr\.?|Sr\.?|II|III|IV|M\.D\.|MD|PhD))?$")
BAD_WORDS = re.compile(r"\b(AI|The|How|Why|What|When|Where|Who|Is|Are|Was|With|And|Of|On|In|For|To|From|Into|"
                       r"Your|You|Our|We|My|This|That|These|Inside|Building|Future|Live|Episode|Podcast|Show|"
                       r"Summit|Debate|Interview|Conversation|Special|Part|Year|Week|Day|Billion|Million|CEO|"
                       r"Founder|Founders|Company|Startup|Startups|Market|Markets|Economy|Deal|Crypto|Tech|"
                       r"America|American|China|Trump|Biden|Elon's|OpenAI|Google|Apple|Meta|Nvidia|Tesla|SpaceX|"
                       r"News|Update|Edition|Bonus|Panel|Roundtable|Keynote|Fireside)\b")

def is_name(s):
    s = s.strip(" .,:;!?\"'“”‘’()")
    if not s or len(s) > 45 or any(ch.isdigit() for ch in s): return False
    if BAD_WORDS.search(s): return False
    return bool(NAME_RE.match(s))

def split_names(s):
    s = re.sub(r"\s*\(.*?\)", "", s)
    parts = re.split(r",\s*(?:and\s+|&\s+)?|\s+&\s+|\s+and\s+|\s+\+\s+|\s+x\s+|\s+vs\.?\s+", s)
    return [p.strip(" .,:;!?\"'“”‘’") for p in parts if p.strip()]

def names_from(s):
    out = []
    for p in split_names(s):
        if is_name(p):
            out.append(p)
        else:
            t = tail_name(p)
            if t: out.append(t)
    return out

PREFIX = re.compile(r"^(?:Dr\.?|Sir|Prof\.?|Professor|General|Gen\.|Admiral|Senator|Sen\.|Gov\.?|Governor|Rabbi|Rep\.|"
                    r"Congressman|Congresswoman|Secretary|President|Ambassador|Coach|Chef|Judge|Mayor|Father|Lord|Dame)\s+")

def clean_name(n):
    n = re.sub(r"^.*?[’']s\s+(?=[A-Z])", "", n)          # "Box's Aaron Levie" -> "Aaron Levie"
    n = re.sub(r"\s+(?:of|from|at)\s+.*$", "", n)        # "Noubar Afeyan of Moderna"
    n = re.sub(r"^[\W\d_]+|[^\w.]+$", "", n)
    while PREFIX.match(n): n = PREFIX.sub("", n)
    toks = n.split()
    # rightmost span (>= 2 tokens, ending at the end) that starts with a recognised first name
    for i in range(len(toks) - 1):
        if known_first(toks[i]) and i > 0 and not known_first(toks[0]):
            return " ".join(toks[i:])
    if len(toks) > 2 and not known_first(toks[0]):
        for i in range(1, len(toks) - 1):
            if known_first(toks[i]): return " ".join(toks[i:])
    return n

def tail_name(p):
    """Longest trailing run of 2-4 capitalised tokens that reads as a name."""
    toks = re.sub(r"^.*[’']s\s+", "", p).split()
    for k in (4, 3, 2):
        if len(toks) >= k:
            cand = " ".join(toks[-k:])
            if is_name(cand) and not re.search(r"\b(?:Co-?Founder|President|Partner|Chief|Director|Head|VP|Professor|Author|Editor|Investor|Chairman|Legendary|Former|Actor|Scientist|Expert)\b", cand):
                return cand
    return ""

# Role/affiliation: the description sentence that introduces the guest.
ROLE_WORD = re.compile(r"\b(?:CEO|CTO|CFO|COO|CPO|CMO|CRO|founder|co-?founder|cofounder|partner|professor|author|president|chair\w*|"
                       r"director|head|investor|scientist|economist|writer|journalist|engineer|executive|officer|host|creator|lead|"
                       r"VP|vice|manager|historian|philosopher|researcher|entrepreneur|editor|analyst|fellow|senator|secretary|"
                       r"minister|governor|mayor|player|athlete|champion|coach|artist|musician|actor|actress|comedian|doctor|"
                       r"physician|psychologist|psychiatrist|neuroscientist|biologist|physicist|chef|designer|GP|MD|PhD|"
                       r"administrator|commissioner|representative|congress\w*|ambassador|general|admiral|novelist|poet|"
                       r"columnist|podcaster|YouTuber|creator|strategist|consultant|advisor|adviser|trader|operator|owner|"
                       r"inventor|pioneer|expert|teacher|lecturer|dean|chancellor|provost|attorney|lawyer|judge)\b", re.I)
TITLE_ROLE = re.compile(r"([A-Z][\w&.'’-]*(?:\s[A-Z][\w&.'’-]*){0,2})(?:[’']s)?\s+((?:Co-?[Ff]ounder(?: and| &)? )?(?:CEO|CTO|CFO|COO|CPO|President|Founder|co-?founder|Partner|GP|Chair(?:man)?)(?: and (?:CEO|President|Founder))?)\s+$")

def role_for(name, title, desc):
    r = _role_for(name, title, desc)
    if r and ROLE_WORD.search(r) and not re.match(r"^(?:living|going|on the show|proof|they|it|is|was|who|and|the show)\b", r, re.I):
        return r
    for text in (title, desc[:1500]):   # "Arm CEO Rene Haas", "Circle Co-Founder and CEO Jeremy Allaire"
        i = text.find(name)
        if i > 0:
            m = TITLE_ROLE.search(text[:i])
            if m and m.group(1) not in ("The", "With", "with", "And"): return f"{m.group(2)} of {m.group(1)}"
    return ""

def _role_for(name, title, desc):
    m = re.search(r"\)\s*-\s*" + re.escape(name) + r",\s*([^,(]{3,120}?),?\s+(?:discuss|explain|shar|talk|join|highlight|break|reflect|announc|outlin|describ|detail|introduc)", desc)
    if m: return m.group(1).strip()
    last = name.split()[-1]
    for sent in re.split(r"(?<=[.!?])\s+", desc[:3000]):
        if name in sent or (last in sent and len(last) > 3):
            m = re.search(re.escape(name) + r"\s*(?:\([^)]*\))?\s*(?:,\s*|\s+(?:is|was|serves as|has been)\s+)(.{5,160}?)(?:[.;]|$)", sent)
            if m: return m.group(1).strip()
    m = re.search(re.escape(name) + r"\s*(?:\(|\s+from\s+|\s+of\s+|,\s*(?=[A-Z][a-z]*\s*(?:CEO|Co-?[Ff]ounder|Founder|Partner|VP|President|GP|Head|CTO|of|at)\b))([^|\]\),]{2,80})", title)
    return m.group(1).strip(" ),") if m else ""

def lead_name(desc, show):
    """Guest named by common intro patterns in the description."""
    d = desc[:1200]
    pats = [r"[Mm]y guests? (?:today|this week|for this episode)?\s*(?:is|are)\s+([^.,;(]+)",
            r"(?:[Tt]oday|[Tt]his week),?\s+(?:I(?:'m| am)| we(?:'re| are))\s+(?:joined by|talking (?:to|with)|speaking with|sitting down with)\s+([^.,;(]+)",
            r"(?:joined by|join(?:s|ed)? by|chop it up with|sits? down with|sat down with|talks? with|talks? to|speaks? with|interviews?|welcome[sd]?|Introducing|chats? with|in conversation with|catch(?:es)? up with)\s+(?:(?:the\s+)?(?:legendary|founder|CEO|investor|author|entrepreneur|special guest|guest)\s+)?([A-Z][^.,;(:)]+)",
            r"^\s*(?:Description\s+)?([A-Z][\w'’.\-]+(?:\s+[A-Z][\w'’.\-]+){1,3})\s*(?:\([^)]*\)\s*)?(?:is|was|,|joins|returns|has|co-?founded|founded|spent|grew|thinks|built|runs|leads)\b"]
    found = []
    for p in pats:
        for m in re.finditer(p, d):
            for n in names_from(m.group(1)):
                if n not in found: found.append(n)
        if found: break
    return found

HOST_ONLY = {
    "All-In": re.compile(r"^\s*\(0:00\)\s*(?:Bestie|Besties|The Besties|Jason|J-?Cal|Chamath|Sacks|Friedberg)\b(?!.{0,80}\b(?:joins|welcome|introduc))", re.I),
    "My First Million": re.compile(r"without a guest|just the two of us|no guest|Sam and Shaan (?:are back|talk|discuss)|"
                                   r"^(?:Episode \d+:\s*)?(?:Sam Parr|Shaan Puri)\s*\([^)]*\)\s*(?:and|&)\s*(?:Sam Parr|Shaan Puri)\s*\([^)]*\)\s*(?:are back|discuss|talk about|brainstorm|riff|share|break down|go over|catch up|rank|react)", re.I),
}

TIM_NON_GUEST = re.compile(
    r"special compilation|compilation devoted|two-for-one|Meditation Monday|"
    r"Tim Ferriss Radio Hour|in-?betweenisode|I answer|answering your questions|answer(?:ed)? the most|drunk-dialing|"
    r"Random Show|Tea Time with Tim|special episode about|devoted to one|showcases two chapters|featuring the book|"
    r"I am in the hot seat|roles are reversed|interviewed me|Interviews Tim Ferriss|Corners Tim Ferriss|I(?:'ve| have) gathered some of the best|"
    r"gathered some of the best advice|roundtable|review of the past year|Past Year Review|This is an unusual episode|"
    r"Tips from|New Tips from|experimental format|a bit different format|How I Built The Tim Ferriss Show|"
    r"Lost Presentation|4-Hour Workweek Revisited|Lessons Learned Traveling|How to Say No\b|How to Succeed in High-Stress|"
    r"One-Person Businesses|My Healing Journey|What I've Learned|Psychedelic News Hour", re.I)
TIM_NON_GUEST_TITLE = re.compile(r"Books I[’']ve Loved|^#?\d*:?\s*Tribe of Mentors|^#?\d*:?\s*Tools of Titans|Fear-Setting|"
                                 r"^Ep\.? ?\d+: (?:Tim Answers|How to Avoid Decision|Do \"Homeopathic|The Top 5 Reasons|The Power of Negative|\"Productivity\")|"
                                 r"^Episode 9: The 9 Habits|Teaser$", re.I)
HANDLE_NAME = re.compile(r"([A-Z][\w.'’-]+(?:\s+(?:de|van|von|el|al|da|[A-Z][\w.'’-]+)){1,3})\s*\(\s*(?:IG:\s*)?@\w+")

LINKED_NAME = re.compile(r"([A-Z][\w.'’-]+(?:\s+(?:de|van|von|el|al|da|[A-Z][\w.'’-]+)){1,3})\s*\(\s*(?:@\w+|https?://(?:www\.)?(?:twitter|x)\.com/@?\w+)")
MFM_HOSTS = {"Sam Parr", "Shaan Puri", "Sam", "Shaan", "Jonathan Gallegos", "Ben Wilson", "Producer Ben", "Ishan Haque"}

def mfm_names(d):
    out = []
    for m in LINKED_NAME.finditer(d[:1500]):
        toks = m.group(1).split()
        n = " ".join(toks[-3:]) if len(toks) > 3 else m.group(1)
        n = clean_name(re.sub(r"^(?:and|with|talks?|guest|Episode \d+:?)\s+", "", n))
        if n and n not in MFM_HOSTS and not any(h in n for h in ("Parr", "Puri")) and n not in out and len(n.split()) >= 2:
            out.append(n)
    return out

def tim_names(t, d):
    out = []
    for m in HANDLE_NAME.finditer(d[:2500]):
        toks = re.split(r"\s+", m.group(1).strip())
        if len(toks) < 2 or toks[-1] not in t or "Ferriss" in toks[-1]:
            continue
        # longest suffix that appears verbatim in the title, else the last two tokens
        n = next((" ".join(toks[-k:]) for k in range(len(toks), 1, -1)
                  if " ".join(toks[-k:]) in t and not toks[-k].endswith(".")), None)
        if n is None:  # first non-initial token before the surname + surname ("Balaji S. Srinivasan" -> "Balaji Srinivasan")
            first = next((x for x in reversed(toks[:-1]) if not re.fullmatch(r"[A-Z]\.", x)), toks[-2])
            n = first + " " + toks[-1]
        n = clean_name(n)
        if len(n.split()) >= 2 and n not in out:
            out.append(n)
    return out

TBPN_TOPIC = re.compile(r"\b(?:Day|Water|Ghibli|Landing|Coin|Timeline|Pardons|Moves|Earnings|Debate|Guide|Deal|Update|Joins|Reactions|"
                        r"Section|Moat|Breaks|Silence|Continues|Bets|Big|Size|Gongs|Interview|Wallet|Sombrita|Mia|Formula|One|Valuation|"
                        r"Tariffs|Market|Markets|Stocks|Crash|Superheroes|Superhero|Takes|Hit|Cooked|Rips|Goated|IPO|CEO|Founder|VC|Fund)\b")

def rule(show, t, d):
    """Return list of guest names from show-specific title rules, or None if no rule applies."""
    if show == "The Tim Ferriss Show":
        n = tim_names(t, d)
        if n: return n
    if show == "Jack Neel Podcast":
        m = re.match(r"^\s*(.+?) (?:Podcast - Interview With|[Ww]ith) Jack Neel", d)
        if m and names_from(m.group(1)): return names_from(m.group(1))
        m = re.search(r"[|│]\s*([^|│]+?)\s*$", t)
        if m and "Jack Neel" not in m.group(1): return names_from(m.group(1))
        m = re.match(r"^(.+?) on ", t)
        return names_from(m.group(1)) if m else None
    if show == "My First Million":
        n = mfm_names(d)
        if n: return n
    if show in ("No Priors", "Sourcery", "All-In", "My First Million"):
        m = re.search(r"\bwith\s+(.+?)$", t)
        if m:
            n = names_from(re.split(r"\s*[:|]\s*", m.group(1))[0])
            if n: return n
        m = re.search(r"[|]\s*([^|]+)$", t)
        if m and names_from(m.group(1)): return names_from(m.group(1))
        m = re.match(r"^(?:#\d+\s*[-–]\s*)?(?:[\w&.]+[’']s\s+)?([^:|]+?):", t)
        if m and names_from(m.group(1)): return names_from(m.group(1))
        return None
    if show == "Lex Fridman Podcast":
        m = re.match(r"^(?:#\d+\s*[–—-]\s*)?(.+?):", t)
        return names_from(m.group(1)) if m else None
    if show == "EconTalk":
        m = re.search(r"\(with ([^)]+)\)", t) or re.match(r"^(.+?) on ", t)
        return names_from(m.group(1)) if m else None
    if show == "Conversations with Tyler":
        m = re.match(r"^(.+?) on ", t)
        return names_from(m.group(1)) if m else None
    if show == "The Tim Ferriss Show":
        m = re.match(r"^(?:Ep\.?|Episode)\s*\d+\s*[:\-–]\s*(?:Dr\.\s+)?(.+?)\s*(?:\(Part \d\)|\(|\s+on\s+|\s+-+\s+|,|$)", t)
        if m and names_from(m.group(1)): return names_from(m.group(1))
        m = re.search(r"(?:—|--|–| - )\s*(?:Dr\.\s+)?([A-Z][\w.'’-]+(?:\s+[A-Z][\w.'’-]+){1,3})\s*(?:\(Repost\))?\s*$", t)
        if m and is_name(m.group(1)): return [m.group(1)]
        m = re.match(r"^(?:#\d+:\s*)?(.+?)\s*(?:—|–| - | on |:|,)", t)
        return names_from(m.group(1)) if m else None
    if show == "Invest Like the Best":
        m = re.match(r"^(.+?)" + DASH + r".*\[Invest Like the Best", t) or re.match(r"^(.+?)\s*[–—-]\s", t)
        return names_from(m.group(1)) if m else None
    if show == "The Knowledge Project":
        m = re.search(r"\|\s*(.+)$", t) or re.match(r"^(?:#\d+\s+)?(.+?):", t)
        return names_from(m.group(1)) if m else None
    if show == "Uncapped with Jack Altman":
        m = re.search(r"\|\s*(.+?)\s+from\s+", t) or re.search(r"\|\s*(.+)$", t)
        return names_from(m.group(1)) if m else None
    if show == "Relentless":
        m = re.match(r"^#\d+\s*-\s*(.+?),", t) or re.search(r"\|\s*(.+?)(?:,|$)", t)
        return names_from(m.group(1)) if m else None
    if show == "Dwarkesh Podcast":
        parts = re.split(r"\s+[–—-]\s+", t, maxsplit=1)
        if len(parts) == 2:
            a = names_from(parts[0]);  b = names_from(parts[1])
            return a or b
        return None
    if show == "Lenny's Podcast":
        m = re.search(r"\|\s*([^|(]+?)\s*(?:\(|$)", t)
        return names_from(m.group(1)) if m else None
    if show == "David Senra":
        m = re.match(r"^(.+?)(?:,| on |:)", t)
        return names_from(m.group(1)) if m else None
    if show == "How I Write":
        m = re.match(r"^(.+?):", t) or re.search(r"\(([^)]+?) Interview\)", t)
        return names_from(m.group(1)) if m else None
    if show == "TBPN":
        m = re.search(r"\|\s*(.+)$", t)
        if m and names_from(m.group(1)): return names_from(m.group(1))
        # early episodes mix guests and topics in a comma list; keep the parts that read as people
        out = [p.strip() for p in re.split(r",\s*|\s+&\s+|\s+and\s+|\s*\|\s*", t)
               if is_name(p.strip()) and not TBPN_TOPIC.search(p) and plausible_person(p.strip())]
        m = re.search(r"(?:full|first|live) (?:interview|conversation) with (?:[A-Z][\w’']+(?: [A-Z][\w’']+)?[’']s (?:Managing Editor, |CEO |founder |Founder and CEO )?|(?:OpenAI|SemiAnalysis|Moltbook|Cloudflare) [\w ]*?(?:CEO|creator|Founder and CEO) )?([A-Z][\w.'’-]+(?:\s+[A-Z][\w.'’-]+){1,3})", d)
        if m and is_name(m.group(1)): out.append(m.group(1))
        for m in re.finditer(r"\(\d+:\d+(?::\d+)?\)\s*-\s*([A-Z][\w.'’-]+(?:\s+[A-Z][\w.'’-]+){1,3})\s*(?:,|\(|\s+(?:discuss|join|is|shares|explain|talk|break|from|of|on))", d):
            n = re.split(r"\.\s", m.group(1).strip())[0]
            if is_name(n) and known_first(n.split()[0]) and n not in out: out.append(n)
        return out or None
    if show == "Cheeky Pint":
        m = re.search(r"\bwith ([A-Z][^,]+?)(?:,| of | from |$)", t)
        return names_from(m.group(1)) if m else None
    return None

# Other Colossus shows syndicated in the Invest Like the Best feed; Knowledge Project solo "Outliers" episodes.
OTHER_SERIES = re.compile(r"\[(?:Business Breakdowns|Founder[’']s Field Guide|Web3 Breakdowns|Art of Investing)|\((?:50X|Invest Like the Best, CLASSICS)|"
                          r"\(50X|^Hash Power|TKP Insights", re.I)
OUTLIERS = re.compile(r"episode of Outliers|\bOutliers\b.{0,40}\bexplore", re.I)

PRECISE = {"Lex Fridman Podcast", "EconTalk", "Conversations with Tyler", "Invest Like the Best", "Uncapped with Jack Altman",
           "Relentless", "Lenny's Podcast", "David Senra", "The Knowledge Project", "Dwarkesh Podcast", "How I Write",
           "Cheeky Pint", "TBPN"}

rows = []
for _, e in eps.iterrows():
    show, t, d = e.show, e.title, e.description
    base = {"episode_id": e.episode_id, "show": show, "date": e.date, "title": t, "source": e.source}
    if (e.episode_type == "trailer" or NON_GUEST.search(t) or OTHER_SERIES.search(t) or OUTLIERS.search(d[:600])
            or (show == "The Tim Ferriss Show" and (TIM_NON_GUEST.search(t + " " + d[:700]) or TIM_NON_GUEST_TITLE.search(t)))):
        rows.append({**base, "guest_name": "", "role": "", "status": "non_guest", "method": "nonguest_rule"}); continue
    if show in HOST_ONLY and HOST_ONLY[show].search(d) and not (rule(show, t, d) or []):
        rows.append({**base, "guest_name": "", "role": "", "status": "non_guest", "method": "host_only"}); continue
    names = rule(show, t, d)
    method = "title_rule"
    if not names:
        names = lead_name(d, show); method = "desc_rule"
    hosts = HOSTS.get(show, [])
    names = [n for n in names if n not in hosts and not any(n == h.split()[0] for h in hosts)]
    if not names and show == "TBPN":   # daily show: no named guest means a host-only segment
        rows.append({**base, "guest_name": "", "role": "", "status": "non_guest", "method": "host_only"}); continue
    if not names and show == "My First Million" and LINKED_NAME.search(d[:1500]):
        rows.append({**base, "guest_name": "", "role": "", "status": "non_guest", "method": "host_only"}); continue
    if not names:
        rows.append({**base, "guest_name": "", "role": "", "status": "unresolved", "method": ""}); continue
    names = [clean_name(n) for n in names]
    names = [n for n in names if n and n not in hosts]
    if not names:
        rows.append({**base, "guest_name": "", "role": "", "status": "unresolved", "method": ""}); continue
    for n in dict.fromkeys(names):
        conf = "high" if (len(n.split()) >= 2 and known_first(n.split()[0]) and
                          (show in PRECISE or n in d)) else "review"
        rows.append({**base, "guest_name": n, "role": role_for(n, t, d), "status": "guest",
                     "method": method, "confidence": conf})

out = pd.DataFrame(rows)
out.to_csv("data/raw/guests_auto.csv", index=False)
ep = out.groupby(["show", "episode_id"]).status.first().reset_index()
summ = ep.groupby(["show", "status"]).size().unstack(fill_value=0)
summ["guest_rows"] = out[out.status == "guest"].groupby("show").size()
print(summ.to_string())
print(out.groupby("method").size())
