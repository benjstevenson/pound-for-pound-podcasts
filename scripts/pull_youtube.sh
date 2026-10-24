#!/usr/bin/env bash
# Phase 1: list every long-form upload on each show's YouTube channel (flat, no downloads).
set -u
cd "$(dirname "$0")/.."
while IFS='|' read -r show url; do
  out="data/raw/youtube/$(echo "$show" | tr ' ' '_' | tr -cd 'A-Za-z0-9_-').tsv"
  yt-dlp --flat-playlist --ignore-errors \
    --print "%(id)s	%(duration)s	%(title)s" "$url/videos" > "$out" 2>/dev/null
  echo "$show: $(wc -l < "$out") videos"
done <<'LIST'
All-In|https://www.youtube.com/@allin
Dwarkesh Podcast|https://www.youtube.com/@DwarkeshPatel
TBPN|https://www.youtube.com/@TBPNLive
Sourcery|https://www.youtube.com/@SourceryVC
Relentless|https://www.youtube.com/channel/UCxYhf1bmbsXLU1ClPNS2P6g
Jack Neel Podcast|https://www.youtube.com/@JackNeel
No Priors|https://www.youtube.com/@NoPriorsPodcast
Lenny's Podcast|https://www.youtube.com/@LennysPodcast
Uncapped with Jack Altman|https://www.youtube.com/@UncappedPod
David Senra|https://www.youtube.com/@DavidSenra
How I Write|https://www.youtube.com/@DavidPerellChannel
Cheeky Pint|https://www.youtube.com/@CheekyPint
My First Million|https://www.youtube.com/@MyFirstMillionPod
LIST
