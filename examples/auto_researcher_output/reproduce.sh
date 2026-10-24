#!/bin/sh
set -eu
set -x
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RUN_ID=${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT="$ROOT/experiments/runs/$RUN_ID"
if [ -e "$OUT" ]; then
  echo "run directory already exists: $OUT" >&2
  exit 2
fi
python3 "$ROOT/experiments/run_experiment.py" --out "$OUT"
sha256sum "$ROOT/experiments/run_experiment.py" "$OUT"/results.jsonl \
  "$OUT"/metadata.json "$OUT"/failures.jsonl "$OUT"/SHA256SUMS
