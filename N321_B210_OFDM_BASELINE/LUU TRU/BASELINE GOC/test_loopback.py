#!/usr/bin/env python3
"""Exercise the GRC's OFDM settings without opening a USRP or transmitting RF."""
import ast
import argparse
from pathlib import Path
import time
from gnuradio import blocks, digital, gr
from check_rx import expected_payload, settings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload-bps',type=int,choices=[1,2])
    parser.add_argument('--sync-threshold',type=float,default=0.9)
    args=parser.parse_args()
    cfg = settings()
    expected = expected_payload()
    fft_len = ast.literal_eval(cfg['fft_len']['value'])
    # These expressions come from the local, trusted GRC, with only range/list enabled.
    def params(name):
        p = cfg[name]
        def value(key):
            return eval(p[key], {'__builtins__': {}, 'list': list, 'range': range}, {'fft_len': fft_len})
        return dict(fft_len=fft_len, cp_len=value('cp_len'),
                    occupied_carriers=value('occupied_carriers'),
                    pilot_carriers=value('pilot_carriers'), pilot_symbols=value('pilot_symbols'),
                    sync_word1=value('sync_word1'), sync_word2=value('sync_word2'),
                    bps_header={'BPSK': 1, 'QPSK': 2}[ast.literal_eval(p['header_mod'])],
                    bps_payload=({'BPSK': 1, 'QPSK': 2}[ast.literal_eval(p['payload_mod'])]
                                 if args.payload_bps is None else args.payload_bps),
                    scramble_bits=value('scramble_bits'), debug_log=False)

    tb = gr.top_block()
    source = blocks.vector_source_b(list(expected), True)
    tagged = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, len(expected), 'packet_len')
    tx = digital.ofdm_tx(packet_length_tag_key='packet_len', **params('digital_ofdm_tx_0'))
    scale = blocks.multiply_const_cc(eval(cfg['tx_scale']['value'], {'__builtins__': {}}, {'fft_len': fft_len}))
    throttle = blocks.throttle(gr.sizeof_gr_complex, ast.literal_eval(cfg['samp_rate']['value']), True)
    from isac_ofdm_modem import ofdm_rx
    rx = ofdm_rx(packet_length_tag_key='rx_len', frame_length_tag_key='frame_rx_len',
                 sync_threshold=args.sync_threshold,expected_payload_bytes=len(expected),**params('digital_ofdm_rx_0'))
    sink = blocks.vector_sink_b()
    tb.connect(source, tagged, tx, scale, throttle, rx, sink)
    tb.start()
    try:
        time.sleep(1.5)
    finally:
        tb.stop()
        tb.wait()
    data = bytes(sink.data())
    packets = len(data) // len(expected)
    assert packets >= 10, f'Too few decoded packets: {packets}'
    assert len(data) % len(expected) == 0, 'Partial payload'
    assert data == expected * packets, 'Decoded payload mismatch'
    output = Path(__file__).resolve().parent / 'loopback_payload.bin'
    output.write_bytes(data)
    print(f'PASS: {packets} matching payloads, {len(data)} bytes; no hardware/RF used.')
    print(f'Header guard accepted={rx.header_guard.accepted} rejected={rx.header_guard.rejected}')
    print(f'Capture: {output}')


if __name__ == '__main__':
    main()
