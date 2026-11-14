#!/usr/bin/env python3
"""Short headless RF test. N321 RF0 transmits a gated +50 kHz tone.

Checks both B210 frontends and antenna selections to diagnose enclosure wiring.
TX gain stays at 10 dB; tone amplitude is 0.01. No payload files are modified.
"""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from gnuradio import analog, blocks, gr, uhd

ROOT = Path(__file__).resolve().parent
RATE = 500000
FREQ = 2450000000


def summarize(samples):
    x = np.asarray(samples, dtype=np.complex64)
    if len(x) < 4096:
        raise RuntimeError(f'Insufficient RX samples: {len(x)}')
    x = x[-min(len(x), 131072):]
    n = 4096
    x = x[:len(x) // n * n].reshape(-1, n)
    w = np.hanning(n)
    power = np.mean(np.abs(np.fft.fftshift(np.fft.fft(x * w, axis=1), axes=1)) ** 2,
                    axis=0) / np.sum(w) ** 2
    f = np.fft.fftshift(np.fft.fftfreq(n, 1 / RATE))
    band = np.flatnonzero((f > 25000) & (f < 75000))
    peak = band[np.argmax(power[band])]
    wide = np.flatnonzero(abs(f) > 15000)
    wide_peak = wide[np.argmax(power[wide])]
    near = np.flatnonzero(abs(f) > 1000)
    near_peak = near[np.argmax(power[near])]
    return dict(samples=int(x.size), rms_dbfs=float(10*np.log10(np.mean(abs(x)**2)+1e-30)),
                peak_hz=float(f[peak]), peak_dbfs=float(10*np.log10(power[peak]+1e-30)),
                wide_peak_hz=float(f[wide_peak]), wide_peak_dbfs=float(10*np.log10(power[wide_peak]+1e-30)),
                non_dc_peak_hz=float(f[near_peak]), non_dc_peak_dbfs=float(10*np.log10(power[near_peak]+1e-30)),
                band_floor_dbfs=float(10*np.log10(np.median(power[band])+1e-30)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--amplitude', type=float, default=0.01, choices=[0.01, 0.1])
    parser.add_argument('--output', default='diagnose_rf_results.json')
    parser.add_argument('--tx-rate-factor', type=int, default=1, choices=[1, 8],
                        help='Experimental device-rate test; logical tone and B210 stay at 500 kS/s')
    parser.add_argument('--settle', type=float, default=0.15)
    args = parser.parse_args()
    tb = gr.top_block()
    rx = uhd.usrp_source('type=b200,serial=F4A11D,master_clock_rate=16e6',
                         uhd.stream_args(cpu_format='fc32', otw_format='sc16', channels=[0, 1]))
    rx.set_subdev_spec('A:A A:B', 0)
    rx.set_samp_rate(RATE)
    for ch in (0, 1):
        rx.set_center_freq(FREQ, ch)
        rx.set_rx_agc(False, ch)
        rx.set_gain(20, ch)
        rx.set_antenna('RX2', ch)
    tx = uhd.usrp_sink('type=n3xx,addr=192.168.180.3,mgmt_addr=192.168.3.102,master_clock_rate=200e6',
                       uhd.stream_args(cpu_format='fc32', otw_format='sc16', channels=[0]), '')
    tx.set_subdev_spec('A:0', 0)
    tx.set_samp_rate(RATE * args.tx_rate_factor)
    tx.set_center_freq(FREQ, 0)
    tx.set_antenna('TX/RX', 0)
    tx.set_gain(10, 0)
    tone = analog.sig_source_c(RATE, analog.GR_COS_WAVE, 50000, args.amplitude)
    gate = blocks.multiply_const_cc(0)
    sinks = [blocks.vector_sink_c(), blocks.vector_sink_c()]
    tb.connect(tone, gate, tx)
    for ch, sink in enumerate(sinks):
        tb.connect((rx, ch), sink)
    report = dict(config=dict(tone_amplitude=args.amplitude, tx_rate=tx.get_samp_rate(), rx_rate=rx.get_samp_rate(),
                              tx_frequency=tx.get_center_freq(0), tx_gain=tx.get_gain(0),
                              tx_antenna=tx.get_antenna(0), tx_subdev=str(tx.get_subdev_spec(0)),
                              rx_subdev=str(rx.get_subdev_spec(0)),
                              rx_frequencies=[rx.get_center_freq(ch) for ch in (0,1)],
                              rx_lo_locked=[str(rx.get_sensor('lo_locked', ch)) for ch in (0,1)]),
                  measurements=[])
    print('ACTUAL CONFIG', report['config'], flush=True)
    tb.start()
    try:
        for gain in (40, 60):
            for antenna in ('RX2', 'TX/RX'):
                for ch in (0,1):
                    rx.set_gain(gain, ch)
                    rx.set_antenna(antenna, ch)
                gate.set_k(0)
                time.sleep(0.25)
                for enabled in (0,1,0):
                    gate.set_k(enabled)
                    time.sleep(args.settle)
                    for sink in sinks:
                        sink.reset()
                    time.sleep(0.35)
                    row = dict(rx_gain=gain, actual_gains=[rx.get_gain(ch) for ch in (0,1)],
                               antenna=antenna, tx_enabled=enabled,
                               channels=[summarize(sink.data()) for sink in sinks])
                    report['measurements'].append(row)
                    print(json.dumps(row), flush=True)
    finally:
        gate.set_k(0)
        tb.stop()
        tb.wait()
        (ROOT/args.output).write_text(json.dumps(report, indent=2))
    print('RF test finished; TX stream stopped.', flush=True)


if __name__ == '__main__':
    main()
