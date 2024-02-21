#!/usr/bin/env bash

set -eux

export VIV_RUN_MODE=persist

ROOT="$(git rev-parse --show-toplevel)"

function viv {
  python3 <(curl -fsSL viv.dayl.in/viv.py) run "$@"
}

mkdir -p "$ROOT/docs/cli"
doc="$ROOT/docs/cli.md"
echo "# CLI Reference" > "$doc"

printf "\n## %s\n" "pycashier" >> "$doc"
viv yartsu -- -o "${ROOT}/docs/svgs/pycashier.svg" -- pycashier -h
printf "\n![pycashier](svgs/%s)\n" "pycashier.svg" >> "$doc"

for cmd in receipt extract merge scrna; do
  file="pycashier-${cmd}.svg"
  viv yartsu -- -w 115 -o "${ROOT}/docs/svgs/$file" -- pycashier $cmd -h
  printf "\n## %s\n" "pycashier $cmd" >> "$doc"
  printf "\n![pycashier %s](svgs/%s)\n" "$cmd" "$file" >> "$doc"
done
