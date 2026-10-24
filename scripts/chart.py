"""Phase 6: the P4P chart -> output/p4p_chart.png and output/p4p_chart.svg.

x = show size (Spotify ratings, log scale; TBPN adjusted, see data/size_adjustments.csv)
y = show guest score (mean Guest Weight of the top 50 guests)
Dashed line = the OLS fit ("expected for its size"); the area above it is shaded.
Built for an X post read on a phone: square, large type, every show labelled directly.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FixedLocator, NullLocator

r = pd.read_csv("output/rankings.csv")
x, y = r["size"].to_numpy(float), r.guest_score.to_numpy(float)
b, a = np.polyfit(np.log10(x), y, 1)

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
ABOVE, BELOW, SHADE = "#2a78d6", "#a3a29c", "#2a78d6"
FONT = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "svg.fonttype": "path"})

# label offsets in points (dx, dy) and alignment, hand-placed to avoid collisions
LABEL = {
    "TBPN": (-14, 6, "right"),
    "Conversations with Tyler": (0, 30, "center"),
    "No Priors": (-12, 12, "right"),
    "How I Write": (12, -16, "left"),
    "EconTalk": (-16, -16, "right"),
    "Invest Like the Best": (14, 12, "left"),
    "The Tim Ferriss Show": (-14, 0, "right"),
    "Sourcery": (12, 0, "left"),
    "The Knowledge Project": (14, -2, "left"),
    "All-In": (-14, 0, "right"),
    "Uncapped with Jack Altman": (0, -17, "center"),
    "Lex Fridman Podcast": (0, -19, "center"),
    "David Senra": (12, -2, "left"),
    "Dwarkesh Podcast": (14, -2, "left"),
    "Cheeky Pint": (12, -2, "left"),
    "My First Million": (14, -2, "left"),
    "Lenny's Podcast": (14, -2, "left"),
    "Jack Neel Podcast": (14, -2, "left"),
    "Relentless": (12, 0, "left"),
}
SHORT = {"Conversations with Tyler": "Conversations\nwith Tyler", "Uncapped with Jack Altman": "Uncapped",
         "The Tim Ferriss Show": "Tim Ferriss", "Lex Fridman Podcast": "Lex Fridman", "The Knowledge Project":
         "Knowledge Project", "Dwarkesh Podcast": "Dwarkesh", "Invest Like the Best": "Invest Like\nthe Best",
         "Jack Neel Podcast": "Jack Neel", "Lenny's Podcast": "Lenny's Podcast"}

fig, ax = plt.subplots(figsize=(10, 10), dpi=160)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
XMIN, XMAX, YMIN, YMAX = 55, 160_000, 15, 105
xs = np.logspace(np.log10(XMIN), np.log10(XMAX), 200)
fit = a + b * np.log10(xs)
ax.fill_between(xs, fit, YMAX, color=SHADE, alpha=0.07, lw=0, zorder=0)
ax.plot(xs, fit, ls=(0, (5, 4)), color=INK2, lw=2, zorder=1)

above = y > a + b * np.log10(x)
for sel, col in [(~above, BELOW), (above, ABOVE)]:
    ax.scatter(x[sel], y[sel], s=150, color=col, edgecolor=SURFACE, linewidth=2, zorder=3)

top5 = set(r.show.head(5))
for _, row in r.iterrows():
    dx, dy, ha = LABEL[row.show]
    name = SHORT.get(row.show, row.show)
    is_top = row.show in top5
    text = f"{name}  {row.p4p:.0f}×" if is_top and "\n" not in name else (f"{name} {row.p4p:.0f}×" if is_top else name)
    ax.annotate(text, (row["size"], row.guest_score), xytext=(dx, dy), textcoords="offset points", ha=ha,
                va="center", fontsize=15 if is_top else 13.5, fontweight="bold" if is_top else "normal",
                color=INK if is_top else INK2, linespacing=1.05, zorder=4,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1, shrinkA=0, shrinkB=7)
                if abs(dx) + abs(dy) > 24 else None)

# in-plot annotations for the line and the shaded area
ax.text(62, 103, "Punching above its weight", fontsize=17, fontweight="bold", color=ABOVE, va="top")
ax.text(62, 99.2, "Books bigger guests than its audience predicts", fontsize=13, color=INK2, va="top")
lx = 30_000
ax.text(lx, a + b * np.log10(lx) - 4.2, "Expected for its size", fontsize=13.5, color=INK2, ha="center", va="top",
        style="italic")

ax.set_xscale("log")
ax.set_xlim(XMIN, XMAX)
ax.set_ylim(YMIN, YMAX)
ax.xaxis.set_major_locator(FixedLocator([100, 1_000, 10_000, 100_000]))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels(["100", "1K", "10K", "100K"])
ax.set_yticks([20, 40, 60, 80, 100])
ax.tick_params(colors=INK2, labelsize=14, length=0, pad=8)
ax.grid(True, color=GRID, lw=1, zorder=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xlabel("Show size: Spotify ratings (log scale)", fontsize=15, color=INK2, labelpad=12)
ax.set_ylabel("Guest score: top 50 guests (0–100)", fontsize=15, color=INK2, labelpad=12)

fig.text(0.06, 0.965, "Pound for pound, the best-booked podcasts in tech", fontsize=24, fontweight="bold",
         color=INK, ha="left", va="top")
fig.text(0.06, 0.925, "Each show's top 50 guests, scored on fame and stature, against audience size.\n"
         "\"12×\" = books like a show 12 times its size.", fontsize=14, color=INK2, ha="left", va="top",
         linespacing=1.35)
fig.text(0.06, 0.016, "Fame: X followers and Wikipedia pageviews, Oct 2026. Stature: hand-graded 1–5 tiers.\n"
         "TBPN's size is adjusted ×1.15 for its off-Spotify audience. Full method and data: see thread.",
         fontsize=11, color=MUTED, ha="left", linespacing=1.4)
fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.15)
fig.savefig("output/p4p_chart.png", facecolor=SURFACE)
fig.savefig("output/p4p_chart.svg", facecolor=SURFACE)
print(f"fit: {a:.2f} + {b:.2f} log10(size)")
