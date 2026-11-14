#!/usr/bin/env bash
set -u
set -o pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit 1
mkdir -p DATA
run_dir="DATA/session_$(date +%Y%m%d_%H%M%S)_$$"
mkdir -p "$run_dir" || exit 1
cp GNU_THU_PHAT.grc "$run_dir/config.grc"
printf 'Log phiên chạy: %s/%s/run.log\n' "$PWD" "$run_dir"
grcc -o . GNU_THU_PHAT.grc > "$run_dir/generate.log" 2>&1 || {
  cat "$run_dir/generate.log"
  exit 1
}
/usr/bin/python3 -u gnu_thu_phat.py 2>&1 | tee "$run_dir/run.log"
run_status=${PIPESTATUS[0]}
if [ -f DATA/rx_payload.bin ]; then
  cp DATA/rx_payload.bin "$run_dir/rx_payload.bin"
  /usr/bin/python3 -u check_rx.py --once --file "$run_dir/rx_payload.bin" > "$run_dir/check.log" 2>&1
  cp DATA/rx_messages.txt "$run_dir/rx_messages.txt"
fi
exit "$run_status"
