#!/usr/bin/env bash
# Rebuild data/messi_contributions.{csv,json} from the sources.
# Needs the saved Transfermarkt pages in raw/transfermarkt/ (not distributed; see README).
set -euo pipefail
cd "$(dirname "$0")"
RAW="${MESSI_RAW:-raw/transfermarkt}"
if ! ls "$RAW"/*.html >/dev/null 2>&1; then
  echo "No saved Transfermarkt pages in $RAW. See README, 'Rebuilding the data'." >&2
  exit 1
fi
bash src/fetch_sources.sh
python3 src/extract_statsbomb.py
python3 src/fetch_wikipedia.py
python3 src/parse_wiki_goals.py > /dev/null
python3 src/parse_wiki_matchboxes.py > /dev/null
python3 src/parse_transfermarkt_stats.py
python3 src/resolve_laliga_assists.py
python3 src/build.py
echo "done: data/messi_contributions.csv and .json"
