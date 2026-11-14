#!/usr/bin/env bash
set -u
set -o pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit 1
run_dir="run_$(date +%Y%m%d_%H%M%S)_$$"
mkdir -p -- "$run_dir" || exit 1
/usr/bin/python3 -u validate_ofdm_rf.py --rx-gain 60 --tx-gain 30 \
  --sample-rate 200000 --payload-bps 1 --sync-threshold 0.3 --seconds 8 \
  --rx-offset-hz 11400 --tx-amplitude 0.8 --output-dir "$run_dir" \
  2>&1 | tee "$run_dir/run.log"
exit "${PIPESTATUS[0]}"
