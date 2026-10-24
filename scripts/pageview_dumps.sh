#!/usr/bin/env bash
# Phase 3b: monthly English Wikipedia pageviews (user agents, all access) from the Wikimedia
# pageview_complete dumps. The REST pageviews API rate-limits this server, so we stream each
# monthly dump, keep only en.wikipedia lines (a contiguous sorted block), stop once it ends,
# and write title<TAB>views per month.
set -u
cd "$(dirname "$0")/.."
month() {
  ym="$1"; y="${ym%-*}"; m="${ym#*-}"
  out="data/raw/pageviews/en_${y}${m}.tsv.gz"
  [ -s "$out" ] && { echo "$ym exists"; return; }
  url="https://dumps.wikimedia.org/other/pageview_complete/monthly/$y/$ym/pageviews-$y$m-user.bz2"
  curl -sS --retry 5 "$url" | bzcat 2>/dev/null | awk -F' ' '
    $1 == "en.wikipedia" { seen = 1; if ($2 != t) { if (t != "") print t "\t" c; t = $2; c = 0 } c += $5; next }
    seen { exit }
    END { if (t != "") print t "\t" c }' | gzip > "$out.part" && mv "$out.part" "$out"
  echo "$ym done: $(zcat "$out" | wc -l) titles"
}
export -f month
printf "%s\n" 2025-10 2025-11 2025-12 2026-01 2026-02 2026-03 2026-04 2026-05 2026-06 2026-07 2026-08 2026-09 \
  | xargs -P 3 -I{} bash -c 'month {}'
