#!/usr/bin/env python3
"""Inspect decoded CRC-passed OFDM byte packets written by GNU Radio file_sink.

This estimates the number of good received payloads, not BER or PER: the GNU
Radio OFDM receiver drops packets that fail CRC, and the repeated message
contains no sequence number with which to count missing frames.
"""
import argparse
from pathlib import Path
import time

DEFAULT_TEXT = 'HELLO N321 -> B210, OFDM AWGN TEST'


def expected_packet(text: str, packet_len: int) -> bytes:
    data = text.encode('ascii')
    if len(data) > packet_len:
        raise ValueError('Message length is greater than packet length')
    return (data + b' ' * packet_len)[:packet_len]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, default=Path('rx_payload.bin'))
    parser.add_argument('--text', default=DEFAULT_TEXT)
    parser.add_argument('--packet-len', type=int, default=64)
    parser.add_argument('--interval', type=float, default=2.0)
    parser.add_argument('--once', action='store_true', help='Read existing file once and exit')
    args = parser.parse_args()
    if args.packet_len < 1 or args.interval <= 0:
        parser.error('packet-len and interval must be positive')
    try:
        expect = expected_packet(args.text, args.packet_len)
    except (UnicodeEncodeError, ValueError) as e:
        parser.error(str(e))

    offset = 0
    pending = b''
    packet_count = 0
    matched = 0
    wrong = 0
    last_ino = None
    print('Expected payload ({} bytes): {!r}'.format(args.packet_len, expect.decode('ascii')),
          flush=True)
    print('NOTE: OFDM CRC-failed packets are dropped before the file sink; this is NOT true BER/PER.',
          flush=True)
    while True:
        if args.file.exists():
            try:
                st = args.file.stat()
                # Running GRC resets the output file; also account for replaced files.
                if st.st_size < offset or (last_ino is not None and last_ino != st.st_ino):
                    offset, pending, packet_count, matched, wrong = 0, b'', 0, 0, 0
                    print('RX file reset; counters cleared', flush=True)
                last_ino = st.st_ino
                with args.file.open('rb') as f:
                    f.seek(offset)
                    chunk = f.read()
                offset += len(chunk)
                pending += chunk
                while len(pending) >= args.packet_len:
                    packet, pending = pending[:args.packet_len], pending[args.packet_len:]
                    packet_count += 1
                    if packet == expect:
                        matched += 1
                    else:
                        wrong += 1
                        if wrong <= 3:
                            print('Unexpected packet {}: {!r}'.format(packet_count,
                                      packet.decode('ascii', errors='replace')), flush=True)
                print('RX accepted={} matched={} unexpected={} bytes={} partial={}'.format(
                    packet_count, matched, wrong, offset, len(pending)), flush=True)
            except (OSError, PermissionError) as e:
                print('Cannot read {}: {}'.format(args.file, e), flush=True)
        else:
            print('Waiting for {} (start GRC in the same directory)'.format(args.file),flush=True)
        if args.once:
            break
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print('Stopped monitoring')
            break

if __name__ == '__main__':
    main()
