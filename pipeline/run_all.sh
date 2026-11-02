#!/bin/bash
# Full extraction: batches of 100 (first pass + sweep). Resumable; stops on a rate limit.
cd "$(dirname "$0")"
for b in 1 2 3 4 5 6; do
  echo "=== batch $b $(date +%H:%M)"
  python3 03_extract.py --jobs 4 --limit 100 > ../data/raw/batch.log; cat ../data/raw/batch.log >> ../data/raw/run.log
  grep -E "batch done|RATE_LIMIT|FAIL|songs to do" ../data/raw/batch.log
  grep -q RATE_LIMIT ../data/raw/batch.log && { echo "STOPPED: rate limit"; exit 2; }
  python3 03b_sweep.py --jobs 4 > ../data/raw/batch.log; cat ../data/raw/batch.log >> ../data/raw/run.log
  grep -E "batch done|RATE_LIMIT|FAIL|songs to sweep" ../data/raw/batch.log
  grep -q RATE_LIMIT ../data/raw/batch.log && { echo "STOPPED: rate limit"; exit 2; }
  left=$(python3 -c "import json,os;print(sum(1 for s in json.load(open('../data/songs.json')) if not os.path.exists(f'../data/raw/mentions/{s[\"id\"]}.json')))")
  echo "songs left: $left"
  [ "$left" = "0" ] && break
done
python3 03b_sweep.py --jobs 4 >> ../data/raw/run.log
echo "ALL DONE $(date +%H:%M)"
