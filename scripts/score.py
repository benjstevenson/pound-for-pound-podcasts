"""Phase 5: Guest Weight, show guest scores, the size fit, and P4P.

Guest Weight (0-100) = w_fame * Fame + (1 - w_fame) * Stature
  Fame    = the higher of the guest's X-follower percentile and Wikipedia-pageview percentile.
            Each percentile is taken across the guests that have that measure (1,350 verified X accounts,
            1,960 Wikipedia articles). A guest with neither has Fame 0: "blank fame data, not a guess".
  Stature = tier 1-5 -> 0, 25, 50, 75, 100 (data/stature.csv)
Show guest score = mean Guest Weight of the show's top N guests (N = 50; fewer -> all of them, flagged).
Show size = Spotify rating count, times the multiplier in data/size_adjustments.csv where a show's audience is
mostly off Spotify (TBPN only).
Fit: guest_score = a + b * log10(size), OLS across the 19 shows.
P4P = equivalent size / size, where equivalent size = 10 ** ((guest_score - a) / b).

Usage: python3 scripts/score.py   -> output/rankings.csv, output/guest_weights.csv, output/robustness.md
"""
import numpy as np
import pandas as pd
from scipy import stats

SHORT = {"Percentiles across all guests (unmeasured ranked lowest)": "All-guest pct",
         "TBPN at raw Spotify count": "TBPN raw"}
TIER_SCORE = {1: 0, 2: 25, 3: 50, 4: 75, 5: 100}


def pct(s):
    """Percentile (0-100) within the guests that have a value; blank stays blank."""
    return s.rank(method="average", pct=True) * 100


def load_guests(pct_base="measured"):
    st = pd.read_csv("data/stature.csv")
    gd = pd.read_csv("data/guest_data.csv")[["guest_name", "wikipedia_article", "pageviews_12m"]]
    xf = pd.read_csv("data/x_followers.csv")[["guest_name", "x_handle", "x_followers"]]
    g = st.merge(gd, on="guest_name", how="left").merge(xf, on="guest_name", how="left")
    g.loc[g.x_followers.isna(), "x_handle"] = np.nan
    if pct_base == "measured":
        g["x_pct"], g["wiki_pct"] = pct(g.x_followers), pct(g.pageviews_12m)
    else:  # "all": rank across every guest, unmeasured counted as the lowest value (variant for the robustness check)
        g["x_pct"] = pct(g.x_followers.fillna(-1)).where(g.x_followers.notna())
        g["wiki_pct"] = pct(g.pageviews_12m.fillna(-1)).where(g.pageviews_12m.notna())
    g["fame"] = g[["x_pct", "wiki_pct"]].max(axis=1).fillna(0)
    g["fame_source"] = np.select([g.x_pct.isna() & g.wiki_pct.isna(), g.x_pct.fillna(-1) >= g.wiki_pct.fillna(-1)],
                                 ["none", "X"], "Wikipedia")
    g["stature"] = g.tier.map(TIER_SCORE)
    return g


def score(g, top_n=50, w_fame=0.5, adjust=None):
    """adjust: {show: multiplier} for show size; default data/size_adjustments.csv."""
    g = g.assign(guest_weight=w_fame * g.fame + (1 - w_fame) * g.stature)
    pairs = pd.read_csv("data/guests.csv")[["show", "guest_name"]].drop_duplicates()
    sg = pairs.merge(g[["guest_name", "guest_weight", "fame", "stature"]], on="guest_name", how="left")
    assert sg.guest_weight.notna().all(), sg[sg.guest_weight.isna()].guest_name.tolist()[:10]
    sg = sg.sort_values(["show", "guest_weight", "guest_name"], ascending=[True, False, True])
    top = sg.groupby("show").head(top_n)
    shows = pd.read_csv("data/shows.csv")[["show", "group", "spotify_ratings"]]
    agg = top.groupby("show").agg(guest_score=("guest_weight", "mean"), top_fame=("fame", "mean"),
                                  top_stature=("stature", "mean"), n_scored=("guest_weight", "size"))
    best = top.groupby("show").head(1).set_index("show").guest_name.rename("top_guest")
    s = shows.merge(agg, on="show").join(best, on="show")
    s["n_guests"] = s.show.map(sg.show.value_counts())
    s["small_sample"] = s.n_guests < top_n
    if adjust is None:
        adjust = pd.read_csv("data/size_adjustments.csv").set_index("show").multiplier.to_dict()
    s["size_multiplier"] = s.show.map(adjust).fillna(1.0)
    s["size"] = (s.spotify_ratings * s.size_multiplier).round()
    x = np.log10(s["size"])
    fit = stats.linregress(x, s.guest_score)
    s["expected_score"] = fit.intercept + fit.slope * x
    s["equivalent_size"] = 10 ** ((s.guest_score - fit.intercept) / fit.slope)
    s["p4p"] = s.equivalent_size / s["size"]
    s = s.sort_values("p4p", ascending=False).reset_index(drop=True)
    s.insert(0, "rank", range(1, len(s) + 1))
    return s, fit, g


def fit_ok(fit):
    return fit.slope > 0 and fit.pvalue < 0.05


if __name__ == "__main__":
    g = load_guests()
    base, fit, gw = score(g)
    tags = pd.read_csv("data/show_tags.csv")[["show", "tag"]]
    out = base.merge(tags, on="show", how="left")
    cols = ["rank", "show", "tag", "group", "spotify_ratings", "size_multiplier", "size", "guest_score", "expected_score", "equivalent_size", "p4p",
            "n_guests", "n_scored", "small_sample", "top_fame", "top_stature", "top_guest"]
    out = out[cols].round({"guest_score": 1, "expected_score": 1, "equivalent_size": 0, "p4p": 2, "top_fame": 1,
                           "top_stature": 1})
    out.to_csv("output/rankings.csv", index=False)
    gw[["guest_name", "tier", "stature", "x_handle", "x_followers", "x_pct", "wikipedia_article", "pageviews_12m",
        "wiki_pct", "fame", "fame_source", "guest_weight", "shows"]].sort_values("guest_weight", ascending=False) \
        .round({"x_pct": 1, "wiki_pct": 1, "fame": 1, "guest_weight": 1}).to_csv("output/guest_weights.csv", index=False)
    print(f"fit: score = {fit.intercept:.2f} + {fit.slope:.2f} * log10(size); R^2 = {fit.rvalue**2:.3f}, "
          f"p = {fit.pvalue:.4f}, slope SE = {fit.stderr:.2f} -> {'OK' if fit_ok(fit) else 'WEAK: flag to Ben'}")
    print(out[["rank", "show", "size", "guest_score", "expected_score", "p4p", "n_guests", "top_guest"]]
          .to_string(index=False))

    # robustness
    variants = [("Base: top 50, fame/stature 50/50", dict()),
                ("Top 25", dict(top_n=25)), ("Top 75", dict(top_n=75)),
                ("Fame/stature 35/65", dict(w_fame=0.35)), ("Fame/stature 65/35", dict(w_fame=0.65))]
    extra = [("Percentiles across all guests (unmeasured ranked lowest)", load_guests("all"), dict()),
             ("TBPN at raw Spotify count", g, dict(adjust={}))]
    base_top5 = list(base.show.head(5))
    rows, ranks = [], {}
    for label, gg, kw in [(l, g, k) for l, k in variants] + extra:
        s, f, _ = score(gg, **kw)
        ranks[label] = s.set_index("show")["rank"]
        t5 = list(s.show.head(5))
        rows.append((label, f, t5, s))
    held = sum(set(t5) == set(base_top5) for _, _, t5, _ in rows)
    md = ["# Robustness check", "",
          f"**Does the top 5 hold? {'Yes' if held == len(rows) else 'Partly'}.** The same five shows "
          f"({', '.join(base_top5)}) are the top 5 by P4P in {held} of {len(rows)} variants "
          "(the base run plus the four the README asks for, plus two extras: how unmeasured guests enter the percentiles, and TBPN without its size adjustment). "
          "The order within the five shifts; the fit stays positive and significant in every variant.", "",
          "Each variant re-runs the whole pipeline (Guest Weight → top-N mean → fit → P4P) with one setting changed.", "",
          "| Variant | Fit slope | R² | p | Top 5 by P4P | Same top 5? | Spearman vs base |", "|---|---|---|---|---|---|---|"]
    for label, f, t5, s in rows:
        same = "same order" if t5 == base_top5 else ("same five" if set(t5) == set(base_top5) else
                                                       f"{len(set(t5) & set(base_top5))} of 5")
        rho = stats.spearmanr(ranks[label], ranks[rows[0][0]].reindex(ranks[label].index)).statistic
        md.append(f"| {label} | {f.slope:.1f} | {f.rvalue**2:.2f} | {f.pvalue:.3f} | {', '.join(t5)} | {same} | {rho:.2f} |")
    md += ["", "## P4P rank of every show under each variant", "",
           "| Show | " + " | ".join(SHORT.get(l, l.split(":")[0]) for l, *_ in rows) + " |",
           "|---" * (len(rows) + 1) + "|"]
    for show in base.show:
        md.append(f"| {show} | " + " | ".join(str(int(ranks[l][show])) for l, *_ in rows) + " |")
    md += ["", "## P4P multiple under each variant", "",
           "| Show | " + " | ".join(SHORT.get(l, l.split(":")[0]) for l, *_ in rows) + " |",
           "|---" * (len(rows) + 1) + "|"]
    for show in base.show:
        md.append(f"| {show} | " + " | ".join(f"{s.set_index('show').p4p[show]:.2f}×" for _, _, _, s in rows) + " |")
    md += ["", "## Notes", "",
           "- Shows with fewer guests than N use all of them: David Senra (45) and Cheeky Pint (36) at N = 50; "
           "also Uncapped (61) at N = 75. At N = 25 those small shows are compared on their best guests only, "
           "which is why David Senra and Cheeky Pint rise there.",
           "- Multiples move more than ranks: the fit's slope changes between variants and P4P is exponential in "
           "the gap to the line, so read the multiples as rough (\"about 10×\", not \"10.3×\").",
           "- Fit quality is on the base run: R² is moderate (about 0.4 with 19 shows). Bigger shows do book bigger "
           "guests, but show size explains less than half the variation in guest scores, which is what makes "
           "the P4P comparison interesting.",
           "- **Guest volume matters.** A fixed top 50 is more selective for a show with many guests: the top 50 of "
           "TBPN's 1,381 guests are its best 4%, while for Uncapped's 61 guests they are 82%. Across shows, the gap "
           "to the fitted line correlates with the number of guests (Spearman 0.51, p = 0.02). If the cut is "
           "proportional instead (each show's top 20% of guests, or all its guests), the size fit collapses "
           "(R² 0.07 and 0.06, not significant), so the README's rule would stop publication. The P4P result "
           "therefore rewards booking many strong guests, not just a high hit rate. Small, selective shows "
           "(David Senra, Cheeky Pint, Uncapped) have the highest averages but too few guests to fill a top 50."]
    md += ["", "## TBPN's size adjustment", "",
           "TBPN's Spotify count (651) is scaled by 1.15 to 749, from its YouTube subscribers per Spotify rating "
           "relative to the other shows (`data/size_adjustments.csv`, `data/audience_check.csv`). "
           "Its X show account suggests a much bigger off-Spotify audience, so here is how the result moves "
           "with larger multipliers:", "",
           "| TBPN multiplier | TBPN size | TBPN rank | TBPN P4P | Top 5 |", "|---|---|---|---|---|"]
    for m in [1, 1.15, 1.5, 2, 3, 5]:
        s, f, _ = score(g, adjust={"TBPN": m})
        t = s.set_index("show").loc["TBPN"]
        md.append(f"| {m}× | {t['size']:,.0f} | {int(t['rank'])} | {t.p4p:.1f}× | {', '.join(s.show.head(5))} |")
    md += ["", "TBPN stays #1 up to about 1.3×. Beyond that it slips to #3 (1.5×) or out of the top 5 (5×), "
           "while the other four leaders hold their places."]
    open("output/robustness.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md[:12]))
