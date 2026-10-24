"""Phase 6: a 5:2 cover image for the X Article -> output/p4p_cover.png.

The main scatter (scripts/chart.py) re-laid out for the Article card's wide format: same data, fit line, shading
and palette, with labels re-placed for the wider canvas.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects
from matplotlib.ticker import FixedLocator, NullLocator

r = pd.read_csv("output/rankings.csv")
x, y = r["size"].to_numpy(float), r.guest_score.to_numpy(float)
b, a = np.polyfit(np.log10(x), y, 1)

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
ABOVE, BELOW, SHADE = "#2a78d6", "#a3a29c", "#2a78d6"
FONT = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT})

# label offsets in points (dx, dy) and alignment for the wide layout
LABEL = {
    "TBPN": (-12, 4, "right"),
    "Conversations with Tyler": (0, 22, "center"),
    "No Priors": (-11, 4, "right"),
    "How I Write": (10, -12, "left"),
    "EconTalk": (-8, -15, "right"),
    "Invest Like the Best": (11, 4, "left"),
    "The Tim Ferriss Show": (11, 0, "left"),
    "Sourcery": (10, 0, "left"),
    "The Knowledge Project": (10, -1, "left"),
    "All-In": (10, -11, "left"),
    "Uncapped with Jack Altman": (10, -9, "left"),
    "Lex Fridman Podcast": (0, -14, "center"),
    "David Senra": (10, -2, "left"),
    "Dwarkesh Podcast": (10, -2, "left"),
    "Cheeky Pint": (10, -2, "left"),
    "My First Million": (10, -8, "left"),
    "Lenny's Podcast": (10, -2, "left"),
    "Jack Neel Podcast": (10, 0, "left"),
    "Relentless": (10, 0, "left"),
}
SHORT = {"Conversations with Tyler": "Conversations\nwith Tyler", "Uncapped with Jack Altman": "Uncapped", "The Tim Ferriss Show": "Tim Ferriss",
         "Lex Fridman Podcast": "Lex Fridman", "The Knowledge Project": "Knowledge Project",
         "Dwarkesh Podcast": "Dwarkesh", "Jack Neel Podcast": "Jack Neel"}

fig, ax = plt.subplots(figsize=(15, 6), dpi=120)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
XMIN, XMAX, YMIN, YMAX = 50, 400_000, 18, 100
xs = np.logspace(np.log10(XMIN), np.log10(XMAX), 200)
fit = a + b * np.log10(xs)
ax.fill_between(xs, fit, YMAX, color=SHADE, alpha=0.07, lw=0, zorder=0)
ax.plot(xs, fit, ls=(0, (5, 4)), color=INK2, lw=2, zorder=1)

above = y > a + b * np.log10(x)
for sel, col in [(~above, BELOW), (above, ABOVE)]:
    ax.scatter(x[sel], y[sel], s=110, color=col, edgecolor=SURFACE, linewidth=1.8, zorder=3)

top5 = set(r.show.head(5))
for _, row in r.iterrows():
    dx, dy, ha = LABEL[row.show]
    is_top = row.show in top5
    name = SHORT.get(row.show, row.show)
    text = (f"{name} {row.p4p:.0f}×" if "\n" in name else f"{name}  {row.p4p:.0f}×") if is_top else name
    ax.annotate(text, (row["size"], row.guest_score), xytext=(dx, dy), textcoords="offset points", ha=ha,
                va="center", linespacing=1.0, fontsize=14 if is_top else 12.5, fontweight="bold" if is_top else "normal",
                color=INK if is_top else INK2, zorder=4,
                path_effects=[patheffects.withStroke(linewidth=4, foreground=SURFACE)])

ax.text(56, 97, "Punching above its weight", fontsize=17, fontweight="bold", color=ABOVE, va="top")
ax.text(56, 90.5, "Books bigger guests than its audience predicts", fontsize=12.5, color=INK2, va="top")
lx = 240_000
ax.text(lx, a + b * np.log10(lx) - 12, "Expected for its size", fontsize=12.5, color=INK2, ha="center",
        va="top", style="italic")

ax.set_xscale("log")
ax.set_xlim(XMIN, XMAX)
ax.set_ylim(YMIN, YMAX)
ax.xaxis.set_major_locator(FixedLocator([100, 1_000, 10_000, 100_000]))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels(["100", "1K", "10K", "100K"])
ax.set_yticks([20, 40, 60, 80, 100])
ax.tick_params(colors=INK2, labelsize=12, length=0, pad=6)
ax.grid(True, color=GRID, lw=1, zorder=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xlabel("Show size: Spotify ratings (log scale)", fontsize=12.5, color=INK2, labelpad=8)
ax.set_ylabel("Guest score", fontsize=12.5, color=INK2, labelpad=8)

fig.text(0.045, 0.955, "Pound for pound, the best-booked podcasts in tech", fontsize=26, fontweight="bold",
         color=INK, ha="left", va="top")
fig.subplots_adjust(left=0.07, right=0.985, top=0.85, bottom=0.13)
fig.savefig("output/p4p_cover.png", facecolor=SURFACE)
