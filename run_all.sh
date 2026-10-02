#!/bin/sh
# Regenerates every number in README.md, in order, into results/.
# Needs VILLAGE_DATA (the downloaded dataset) and GITHUB_TOKEN (read-only, for
# gh_commits.py). Takes about an hour on a 2 GB machine; check2.py is most of it.
set -e
cd "$(dirname "$0")"
mkdir -p results
python3 teste_tokens.py
python3 pares.py
python3 check2.py
[ -n "$SKIP_GH" ] || python3 gh_commits.py
python3 report2.py sha        > results/per-model.txt
python3 vizinhanca.py 14 1 20 > results/neighbourhood.txt
python3 comprimento2.py       > results/long-hashes.txt
echo "done: results/"
