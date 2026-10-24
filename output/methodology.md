# Methodology

**The question:** which tech and business podcasts book guests far above what their audience size would predict?

## The short version

1. I scored every guest on 19 shows (4,233 people, every episode ever): half fame (X followers or Wikipedia pageviews), half stature (a 1–5 grade for what they've achieved).
2. Each show's score is the average of its top 50 guests. Bigger shows book bigger guests, so I fitted the line that predicts guest score from Spotify rating count.
3. "Pound for pound" is how big a show would normally have to be to book like that, divided by its actual size.

## Step by step

**Shows.** I hand-picked 19 tech and business shows: 14 small or mid-sized ones and 5 big reference shows (Lex Fridman, All-In, Tim Ferriss, TBPN, My First Million). Joe Rogan and Diary of a CEO were left out as not tech, and too big to be useful.

**Episodes.** I pulled each show's full back catalogue from its RSS feed, back to episode 1: 7,317 episodes in all, going back to 2006 (EconTalk).
- Dropped: solo and host-only episodes, clips, trailers, "best of" episodes, reruns, Q&As and compilations.
- On All-In and My First Million, only episodes with a named outside guest count.
- A repeat guest counts once per show.

**Guests.** I identified guests from episode titles and descriptions, with about 1,100 episodes checked by hand. That gives 4,233 people and 5,581 show–guest pairs.
- On TBPN, a daily live show, every named guest counts.
- Episodes that are *about* someone are not credited to them. For example, Tim Ferriss's "Lessons from Steve Jobs" episode is credited to its actual guest, Walter Isaacson.

**Guest Weight (0–100)** = 50% Fame + 50% Stature.

- **Fame** is the higher of two percentiles:
  - the guest's X-follower percentile (live counts for 1,350 verified personal accounts, October 2026), and
  - their English Wikipedia pageview percentile (October 2025 to September 2026, 1,959 articles).

  Each percentile is ranked among the guests who have that measure. Taking the higher of the two means a Nobel laureate who barely posts still scores as famous. Guests with neither measure get Fame 0, not a guess; they are mostly early-stage founders and niche practitioners.
- **Stature** is a hand-graded 1–5 tier for what the guest is known for today, scored 0 / 25 / 50 / 75 / 100. When a guest sat between two tiers, I gave the lower one.

| Tier | Meaning | Examples of the bar | Guests |
|---|---|---|---|
| 5 | Era-defining | Founded or led a $100B+ company; head of state; Nobel, Turing or Fields winner; globally famous | 72 |
| 4 | Top of their field | Founded or led a $10B+ company; leads a top AI lab or top-tier VC firm; cabinet-level official; landmark bestselling author; globally known athlete or artist | 318 |
| 3 | Clearly accomplished | $1B+ company founder or senior exec; prominent professor; notable bestselling author; partner at a top fund; well-known journalist | 910 |
| 2 | Established professional | Startup founder, VC, author, executive or academic with a solid record | 1,580 |
| 1 | Emerging or niche | Early-stage founder, creator or practitioner; little public record | 1,353 |

**Show guest score.** The average Guest Weight of the show's top 50 guests. Two shows have fewer than 50 guests and use all of them, which makes them small samples: Cheeky Pint (36) and David Senra's interview show (45).

**Show size.** The show's Spotify rating count, with one adjustment:
- TBPN is watched mostly live on X and YouTube.
- On YouTube, it has 1.15× as many subscribers per Spotify rating as the median show here, so its size is 749 rather than 651.
- Its X following would justify much more; see the caveats.

**The fit.** Across the 19 shows, a straight-line fit of guest score on log₁₀(show size) gives:

> guest score = 30.5 + 12.8 × log₁₀(size), R² = 0.42, p = 0.003

Every tenfold increase in audience buys about 13 points of guest score.

**Pound for pound (P4P).**
- The size a show would "need" to book its guests is `equivalent size = 10 ^ ((guest score − 30.5) / 12.8)`.
- P4P = equivalent size ÷ actual size.
- "TBPN books like a show 15× its size" means a typical show would need about 15 times TBPN's audience to land guests as heavy as TBPN's top 50.

**Robustness.** The same five shows lead in every variant:
- using the top 25 or top 75 guests instead of the top 50,
- weighting fame and stature 35/65 or 65/35,
- an alternative way of ranking fame, and
- leaving TBPN's size unadjusted.

The order within the five shifts. The details are in `robustness.md`.

## Caveats

- **Fame is measured today, not when the guest appeared.** Sam Altman on EconTalk in 2014 counts with his 2026 fame. Shows with long back catalogues get credit for guests who became famous later; that is partly booking skill and partly luck.
- **Rating counts are cumulative.** Older shows have had more years to collect ratings, so they look bigger than their current audience, which lowers their P4P. Newer shows such as Cheeky Pint, David Senra's interview show and Uncapped look smaller than their real reach.
- **The show list was hand-picked.** The fitted line, and so every multiple, depends on which 19 shows are in it. A different set of comparison shows would move the line.
- **Spotify ratings are a rough proxy for audience.** Shows that live on YouTube or X are under-counted. TBPN gets a small adjustment, but its X account (1.6M followers) suggests its true audience is much bigger. Above about 1.3× its Spotify count, TBPN would drop from #1. At 1.5× it is #3; at 3× it is #5.
- **The top 50 rewards volume.** A show with 1,381 guests (TBPN) picks its top 50 from a much deeper pool than one with 61 (Uncapped). P4P measures "has booked a lot of heavyweights", not "hit rate per episode". Scored on a hit-rate basis, such as each show's top 20% of guests, the link between size and guest score disappears.
- **Stature is a judgement call.** I graded 4,233 people by hand against a written rubric. Individual grades can be argued with; the robustness checks show the top 5 doesn't hinge on the fame/stature balance.
- **Matching is imperfect.** Guests were matched to Wikipedia and X automatically, then checked. A few percent of matches are probably still wrong. Wrong X accounts can only raise a guest's fame, never lower it, because Fame takes the higher of the two measures.
- **The multiples are rough.** P4P is exponential in the distance from the line, so read "15×" as "roughly 10 to 20×".

## Data

- **Show results:** `output/rankings.csv`, with one row per show: score, expected score, P4P and the show tag (independent, firm-backed, or host is the draw).
- **Guest Weights:** `output/guest_weights.csv`, with every guest's inputs.
- **Top guests:** `output/heavyweights.csv`, the 100 heaviest guests and the shows they appeared on.
- **Inputs:**
  - `data/episodes.csv`
  - `data/guests.csv`
  - `data/stature.csv`
  - `data/guest_data.csv` (Wikipedia data)
  - `data/x_followers.csv`
  - `data/shows.csv`
  - `data/size_adjustments.csv`
- **Scripts:** in `scripts/`. `score.py` reproduces every number above.
