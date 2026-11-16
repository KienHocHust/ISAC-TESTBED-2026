#!/usr/bin/env python3
"""Compare CRC-passed payload bytes with the message configured in the GRC."""
import argparse
import ast
from pathlib import Path
import time
import yaml

ROOT = Path(__file__).resolve().parent


def settings():
    graph = yaml.safe_load((ROOT / 'N321_B210_OFDM_BASELINE.grc').read_text())
    return {b['name']: b['parameters'] for b in graph['blocks']}


def expected_payload():
    cfg = settings()
    text = ast.literal_eval(cfg['message_text']['value'])
    length = ast.literal_eval(cfg['packet_len']['value'])
    data = text.encode('ascii')
    if length <= 0 or not data or len(data) > length:
        raise ValueError('message_text must contain 1..packet_len ASCII bytes')
    return data.ljust(length, b' ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, default=ROOT / 'rx_payload.bin')
    parser.add_argument('--once', action='store_true', help='Exit 0 only if nonempty data matches completely')
    args = parser.parse_args()
    expected = expected_payload()
    print(f'Expected {len(expected)} bytes per payload: {expected!r}', flush=True)
    print('Counts are CRC-passed payloads; these are not BER/PER or transmitted packet counts.', flush=True)
    offset = matched = wrong = 0
    pending = b''
    identity = None
    try:
        while True:
            try:
                with args.file.open('rb') as stream:
                    import os
                    stat = os.fstat(stream.fileno())
                    current = (stat.st_dev, stat.st_ino)
                    if identity != current or stat.st_size < offset:
                        offset = matched = wrong = 0
                        pending = b''
                        identity = current
                        print('New capture: counters reset.', flush=True)
                    stream.seek(offset)
                    chunk = stream.read(1024 * 1024)
                offset += len(chunk)
                pending += chunk
                while len(pending) >= len(expected):
                    packet, pending = pending[:len(expected)], pending[len(expected):]
                    if packet == expected:
                        matched += 1
                        if matched == 1:
                            print(f'First matching payload: {packet!r}', flush=True)
                    else:
                        wrong += 1
                        if wrong <= 3:
                            print(f'Unexpected payload: {packet!r}', flush=True)
                print(f'RX bytes={offset} matched={matched} unexpected={wrong} partial={len(pending)}', flush=True)
                if args.once:
                    # Drain large existing captures before deciding.
                    if len(chunk) == 1024 * 1024:
                        continue
                    good = matched > 0 and wrong == 0 and not pending
                    print('PASS: received message matches.' if good else 'FAIL: no complete matching capture, mismatches, or trailing partial payload.')
                    return 0 if good else 1
            except FileNotFoundError:
                print(f'Waiting for {args.file}', flush=True)
                if args.once:
                    return 1
            time.sleep(2)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
