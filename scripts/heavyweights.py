"""Phase 6: output/heavyweights.csv - the top 100 guests across all 19 shows by Guest Weight, with their shows."""
import pandas as pd

g = pd.read_csv("output/guest_weights.csv")
st = pd.read_csv("data/stature.csv")[["guest_name", "known_for", "reason"]]
h = g.merge(st, on="guest_name", how="left").sort_values(["guest_weight", "fame"], ascending=False).head(100)
h["n_shows"] = h.shows.str.count(";") + 1
h.insert(0, "rank", range(1, len(h) + 1))
h = h[["rank", "guest_name", "guest_weight", "tier", "fame", "fame_source", "x_followers", "pageviews_12m",
       "n_shows", "shows", "reason"]].rename(columns={"reason": "stature_reason", "pageviews_12m": "wikipedia_views_12m"})
h["x_followers"] = h.x_followers.astype("Int64")
h["wikipedia_views_12m"] = h.wikipedia_views_12m.astype("Int64")
h.to_csv("output/heavyweights.csv", index=False)
print(h.head(25)[["rank", "guest_name", "guest_weight", "n_shows", "shows"]].to_string(index=False))
print("shows with most top-100 heavyweights:")
print(h.shows.str.split("; ").explode().value_counts().to_string())
