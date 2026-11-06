#!/usr/bin/env bash
# Clone the two public goal logs the pipeline merges, pinned to the commits used.
set -euo pipefail
WORK="${MESSI_WORKDIR:-$(cd "$(dirname "$0")/.." && pwd)/work}"
mkdir -p "$WORK/ext"
clone() { # repo dir commit
  if [ ! -d "$WORK/ext/$2" ]; then
    git clone -q "https://github.com/$1.git" "$WORK/ext/$2"
  fi
  git -C "$WORK/ext/$2" -c advice.detachedHead=false checkout -q "$3"
}
clone avishek-choudhary/Lionel-Messi-Club-Career-Goals-Analysis Lionel-Messi-Club-Career-Goals-Analysis a29afd3ef8eef4fafe1229ba0a205696cefc51ab
clone raym26/messi-800-goals-dataset messi-800-goals-dataset abc0c52fbecd463100ee6ffda239bf8b6de72693
echo "source repos ready in $WORK/ext"
