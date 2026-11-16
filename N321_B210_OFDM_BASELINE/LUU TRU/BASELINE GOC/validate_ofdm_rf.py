#!/usr/bin/env python3
"""Bounded N321 -> B210 OFDM RF validation, without synthetic noise or GUI.

Reads payload and OFDM parameters from the baseline GRC. This script transmits
RF automatically for the requested duration, then stops both USRP streams.
"""
import argparse
import ast
import json
from pathlib import Path
import time
from gnuradio import blocks, digital, gr, uhd
from check_rx import expected_payload, settings
from isac_ofdm_modem import ofdm_rx

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rx-gain', type=int, default=20, choices=[20, 30, 40, 50, 60])
    parser.add_argument('--tx-gain', type=int, choices=[10, 20, 30])
    parser.add_argument('--sample-rate', type=int, choices=[200000,500000])
    parser.add_argument('--payload-bps',type=int,choices=[1,2])
    parser.add_argument('--sync-threshold',type=float,default=0.9,choices=[0.3,0.5,0.7,0.9])
    parser.add_argument('--management-address',choices=['192.168.3.102','192.168.180.3'])
    parser.add_argument('--seconds', type=int, default=8, choices=range(1, 31))
    parser.add_argument('--rx-offset-hz', type=float, default=0)
    parser.add_argument('--tx-amplitude', type=float, choices=[0.2, 0.5, 0.8],
                        help='Amplitude divided by fft_len to normalize the IFFT before UHD')
    parser.add_argument('--capture-iq', action='store_true', help='Save raw TX/RX IQ for offline diagnosis')
    parser.add_argument('--output-dir', type=Path, default=ROOT.parent/'rf_validation',
                        help='Directory for reports and IQ captures')
    parser.add_argument('--number-sequence', action='store_true',
                        help='Repeat ASCII numbers 1 through 10 in separate 64-byte packets')
    args = parser.parse_args()
    if abs(args.rx_offset_hz)>40000:
        parser.error('RX offset must be within +/-40 kHz')
    cfg = settings()
    payload = expected_payload()
    payloads = ([str(i).encode('ascii').ljust(64, b' ') for i in range(1, 11)]
                if args.number_sequence else [payload])
    payload = payloads[0]
    def value(name):
        return eval(cfg[name]['value'], {'__builtins__': {}},
                    {'fft_len': ast.literal_eval(cfg['fft_len']['value'])})
    rate, freq, fft_len = value('samp_rate'), value('center_freq'), value('fft_len')
    if args.sample_rate is not None:rate=args.sample_rate

    def ofdm_params(name):
        p = cfg[name]
        def expr(key):
            return eval(p[key], {'__builtins__': {}, 'list': list, 'range': range}, {'fft_len': fft_len})
        return dict(fft_len=fft_len, cp_len=expr('cp_len'),
                    occupied_carriers=expr('occupied_carriers'),
                    pilot_carriers=expr('pilot_carriers'), pilot_symbols=expr('pilot_symbols'),
                    sync_word1=expr('sync_word1'), sync_word2=expr('sync_word2'),
                    bps_header={'BPSK': 1, 'QPSK': 2}[ast.literal_eval(p['header_mod'])],
                    bps_payload=({'BPSK': 1, 'QPSK': 2}[ast.literal_eval(p['payload_mod'])]
                                 if args.payload_bps is None else args.payload_bps),
                    scramble_bits=expr('scramble_bits'), debug_log=False)

    rx = uhd.usrp_source(ast.literal_eval(cfg['uhd_usrp_source_0']['dev_addr']),
                         uhd.stream_args(cpu_format='fc32', otw_format='sc16', channels=[0]))
    rx.set_subdev_spec(cfg['uhd_usrp_source_0']['sd_spec0'], 0)
    rx.set_samp_rate(rate)
    rx.set_center_freq(freq+args.rx_offset_hz, 0)
    rx.set_antenna('RX2', 0)
    rx.set_rx_agc(False, 0)
    rx.set_gain(args.rx_gain, 0)
    tx_address=ast.literal_eval(cfg['uhd_usrp_sink_0']['dev_addr'])
    if args.management_address is not None:
        tx_address=','.join(('mgmt_addr='+args.management_address) if x.startswith('mgmt_addr=') else x
                            for x in tx_address.split(','))
    tx = uhd.usrp_sink(tx_address,
                       uhd.stream_args(cpu_format='fc32', otw_format='sc16', channels=[0]), '')
    tx.set_subdev_spec(cfg['uhd_usrp_sink_0']['sd_spec0'], 0)
    tx.set_samp_rate(rate)
    tx.set_center_freq(freq, 0)
    tx.set_antenna('TX/RX', 0)
    tx_gain=value('tx_gain') if args.tx_gain is None else args.tx_gain
    tx.set_gain(tx_gain, 0)
    assert abs(tx.get_samp_rate()-rate)<1 and abs(rx.get_samp_rate()-rate)<1
    source = blocks.vector_source_b(list(b''.join(payloads)), True)
    tagged = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, len(payload), 'packet_len')
    modem_tx = digital.ofdm_tx(packet_length_tag_key='packet_len', **ofdm_params('digital_ofdm_tx_0'))
    tx_scale=value('tx_scale') if args.tx_amplitude is None else args.tx_amplitude/fft_len
    scale = blocks.multiply_const_cc(tx_scale)
    gate = blocks.multiply_const_cc(0)
    modem_rx = ofdm_rx(packet_length_tag_key='rx_len', frame_length_tag_key='frame_rx_len',
                       sync_threshold=args.sync_threshold, expected_payload_bytes=len(payload),
                       **ofdm_params('digital_ofdm_rx_0'))
    sink = blocks.vector_sink_b()
    tb = gr.top_block()
    tb.connect(source, tagged, modem_tx, scale, gate, tx)
    tb.connect(rx, modem_rx, sink)
    out=args.output_dir;out.mkdir(parents=True, exist_ok=True)
    stem=f'ofdm_rx_gain{args.rx_gain}_offset{args.rx_offset_hz:g}_scale{tx_scale:g}'.replace('.','p')
    if args.tx_gain is not None:stem+=f'_txgain{tx_gain}'
    if args.sample_rate is not None:stem+=f'_rate{rate}'
    if args.payload_bps is not None:stem+=f'_bps{args.payload_bps}_thr{args.sync_threshold:g}'.replace('.','p')
    raw_sinks=[]
    if args.capture_iq:
        for name,block in [('rx',rx),('tx',gate)]:
            raw=blocks.file_sink(gr.sizeof_gr_complex,str(out/f'{stem}_{name}_iq.c64'),False)
            tb.connect(block,raw)
            raw_sinks.append(raw)
    print(f'ACTUAL: TX {tx.get_samp_rate()} S/s gain {tx.get_gain(0)} dB; '
          f'RX {rx.get_samp_rate()} S/s gain {rx.get_gain(0)} dB', flush=True)
    tb.start()
    try:
        time.sleep(2)
        gate.set_k(1)
        print('TX enabled: known OFDM payload, no added noise.', flush=True)
        a=time.monotonic(); nt=tx.nitems_read(0); nr=rx.nitems_written(0)
        time.sleep(args.seconds)
        elapsed=time.monotonic()-a
        tx_sps=(tx.nitems_read(0)-nt)/elapsed
        rx_sps=(rx.nitems_written(0)-nr)/elapsed
        gate.set_k(0)
        time.sleep(2)
    finally:
        gate.set_k(0)
        tb.stop()
        tb.wait()
        for raw in raw_sinks:raw.close()
    data=bytes(sink.data())
    packets, partial=divmod(len(data),len(payload))
    received = [data[i:i+len(payload)] for i in range(0,packets*len(payload),len(payload))]
    counts = {p.decode('ascii').rstrip(): received.count(p) for p in payloads}
    matched=sum(p in payloads for p in received)
    good=matched>=10 and matched==packets and partial==0
    if args.number_sequence:
        good = good and all(counts.values())
    out=args.output_dir;out.mkdir(parents=True, exist_ok=True)
    prefix=out/f'ofdm_rx_gain{args.rx_gain}'
    if args.rx_offset_hz or args.tx_amplitude is not None:
        prefix=out/f'ofdm_rx_gain{args.rx_gain}_offset{args.rx_offset_hz:g}_scale{tx_scale:g}'
        # with_suffix would otherwise treat the scale's decimal as an extension.
        prefix=Path(str(prefix).replace(f'_scale{tx_scale:g}',f'_scale{tx_scale:g}'.replace('.','p')))
    if args.tx_gain is not None:prefix=Path(str(prefix)+f'_txgain{tx_gain}')
    if args.sample_rate is not None:prefix=Path(str(prefix)+f'_rate{rate}')
    if args.payload_bps is not None:prefix=Path(str(prefix)+f'_bps{args.payload_bps}_thr{args.sync_threshold:g}'.replace('.','p'))
    prefix.with_suffix('.bin').write_bytes(data)
    report=dict(passed=good, bytes=len(data), matched=matched, unexpected=packets-matched,
                partial_bytes=partial, rx_gain=args.rx_gain, tx_gain=tx_gain,
                rate=rate, tx_observed_sps=tx_sps, rx_observed_sps=rx_sps,
                rx_offset_hz=args.rx_offset_hz, tx_scale=tx_scale,
                payload_bps=args.payload_bps, sync_threshold=args.sync_threshold,
                accepted_headers=modem_rx.header_guard.accepted,
                rejected_headers=modem_rx.header_guard.rejected,
                expected_payload=payload.decode('ascii'),
                note='CRC-passed decoded payloads only; not a BER/PER measurement.')
    if args.number_sequence:
        report.update(expected_payloads=list(counts), received_counts=counts,
                      missing_numbers=[n for n,c in counts.items() if not c],
                      received_sequence=[p.decode('ascii', errors='replace').rstrip() for p in received])
        (out/'TX_SEQUENCE.txt').write_text('\n'.join(list(counts))+'\n')
        (out/'RX_SEQUENCE.txt').write_text('\n'.join(report['received_sequence'])+'\n')
    prefix.with_suffix('.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
    return 0 if good else 1


if __name__=='__main__':
    raise SystemExit(main())
