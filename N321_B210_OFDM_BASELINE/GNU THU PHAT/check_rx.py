#!/usr/bin/env python3
"""Display CRC-passed received bytes and compare with the saved GRC message."""
import argparse
import ast
from pathlib import Path
import time
import yaml
from payload_utils import encode_payload

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--file', type=Path, default=ROOT/'DATA'/'rx_payload.bin')
    args = parser.parse_args()
    graph = yaml.safe_load((ROOT/'GNU_THU_PHAT.grc').read_text())
    cfg = {b['name']: b['parameters'] for b in graph['blocks']}
    text = ast.literal_eval(cfg['message_text']['value'])
    size = ast.literal_eval(cfg['packet_len']['value'])
    expected = encode_payload(text, size)
    print('CÂU KỲ VỌNG: ' + repr(text), flush=True)
    print('Chỉ đếm gói sau CRC; không phải BER/PER.', flush=True)
    output = ROOT/'DATA'/'rx_messages.txt'
    offset = matched = wrong = 0
    pending = b''
    identity = None
    try:
        while True:
            try:
                with args.file.open('rb') as stream:
                    stat = args.file.stat()
                    current = (stat.st_dev, stat.st_ino)
                    if identity != current or stat.st_size < offset:
                        identity = current
                        offset = matched = wrong = 0
                        pending = b''
                        output.write_text('', encoding='utf-8')
                    stream.seek(offset)
                    chunk = stream.read(1024*1024)
                offset += len(chunk)
                pending += chunk
                with output.open('a', encoding='utf-8') as decoded:
                    while len(pending) >= size:
                        packet, pending = pending[:size], pending[size:]
                        good = packet == expected
                        matched += int(good)
                        wrong += int(not good)
                        # Keep raw padding in rx_payload.bin; use repr to show spaces.
                        value = packet.decode('utf-8', errors='replace')
                        shown = value[:len(text)] if good else value
                        line = ('THU ĐÚNG: ' if good else 'KHÁC KỲ VỌNG: ') + repr(shown)
                        decoded.write(line+'\n')
                        if matched <= 3 or not good:
                            print(line, flush=True)
                print(f'bytes={offset} matched={matched} unexpected={wrong} partial={len(pending)}', flush=True)
                if args.once and len(chunk) < 1024*1024:
                    return 0 if matched > 0 and wrong == 0 and not pending else 1
            except FileNotFoundError:
                print('Chờ dữ liệu: '+str(args.file), flush=True)
                if args.once:
                    return 1
            time.sleep(2)
    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
