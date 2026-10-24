"""Phase 6: the top 10 by P4P as a bar chart -> output/p4p_top10.png and output/p4p_top10.svg.

Same palette and type as scripts/chart.py. Bar length = P4P multiple ("books like a show N× its size");
the dashed line at 1× is what a show's size predicts.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

r = pd.read_csv("output/rankings.csv").head(10).iloc[::-1].reset_index(drop=True)

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
TOP5, NEXT5 = "#2a78d6", "#86b6ef"
FONT = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "svg.fonttype": "path"})


def fmt(v):
    return f"{v:.0f}×" if v >= 2.5 else f"{v:.1f}×"


fig, ax = plt.subplots(figsize=(10, 10), dpi=160)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
XMAX = r.p4p.max() * 1.12
ax.set_xlim(0, XMAX)
ax.set_ylim(-0.7, len(r) - 0.3)

H = 0.62
for i, row in r.iterrows():
    top = row["rank"] <= 5
    # bar with a rounded data end, square at the baseline
    ax.add_patch(FancyBboxPatch((0, i - H / 2), row.p4p, H, boxstyle="round,pad=0,rounding_size=0.12",
                                mutation_aspect=1 / (XMAX / len(r) * 0.6), color=TOP5 if top else NEXT5, lw=0, zorder=2))
    ax.add_patch(plt.Rectangle((0, i - H / 2), min(row.p4p, 1.0), H, color=TOP5 if top else NEXT5, lw=0, zorder=2))
    ax.text(row.p4p + XMAX * 0.012, i, fmt(row.p4p), va="center", ha="left", fontsize=17 if top else 15,
            fontweight="bold", color=INK if top else INK2, zorder=3)
    ax.text(-XMAX * 0.02, i + 0.11, f"{int(row['rank'])}. {row.show}", va="center", ha="right",
            fontsize=15.5 if top else 14.5, fontweight="bold" if top else "normal", color=INK if top else INK2)
    ax.text(-XMAX * 0.02, i - 0.25, f"{row.spotify_ratings:,.0f} Spotify ratings" +
            (f" (×{row.size_multiplier:g} = {row['size']:,.0f})" if row.size_multiplier != 1 else ""), va="center", ha="right",
            fontsize=11.5, color=MUTED)

ax.axvline(1, color=INK2, ls=(0, (5, 4)), lw=2, zorder=4)
ax.text(1 + XMAX * 0.012, len(r) - 0.42, "1× = expected for its size", fontsize=12.5, color=INK2, style="italic",
        va="center", ha="left")
ax.axis("off")

fig.text(0.04, 0.965, "Pound for pound, the best-booked podcasts in tech", fontsize=24, fontweight="bold",
         color=INK, ha="left", va="top")
fig.text(0.04, 0.925, "Top 10 of 19 shows. \"15×\" = books guests like a show 15 times its size.", fontsize=14,
         color=INK2, ha="left", va="top")
fig.text(0.04, 0.022, "Guests scored on fame (X followers, Wikipedia pageviews) and stature (hand-graded 1–5 tiers); "
         "each show's top 50 guests.\nTBPN's size is adjusted ×1.15 for its off-Spotify audience. "
         "Full method and data: see thread.", fontsize=11, color=MUTED, ha="left", linespacing=1.4)
fig.subplots_adjust(left=0.37, right=0.96, top=0.87, bottom=0.1)
fig.savefig("output/p4p_top10.png", facecolor=SURFACE)
fig.savefig("output/p4p_top10.svg", facecolor=SURFACE)
