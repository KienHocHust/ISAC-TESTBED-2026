#!/usr/bin/env bash
# Repeat numbers 1..10 over RF for eight seconds; save a separate run each time.
set -u
set -o pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." || exit 1
test_dir="DATA TEST/run_$(date +%Y%m%d_%H%M%S)_$$"
mkdir -p -- "$test_dir" || exit 1
/usr/bin/python3 -u "BASELINE GOC/validate_ofdm_rf.py" --rx-gain 60 --tx-gain 30 \
  --sample-rate 200000 --payload-bps 1 --sync-threshold 0.3 \
  --seconds 8 --rx-offset-hz 11400 --tx-amplitude 0.8 \
  --number-sequence --capture-iq --output-dir "$test_dir" \
  2>&1 | tee "$test_dir/run.log"
exit "${PIPESTATUS[0]}"
