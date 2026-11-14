#!/usr/bin/env python3
"""Measure N321 internal CAL path, without modifying calibration/firmware.

Uses CAL antenna selections as in UHD's official calibration utility, but only
captures a few frames; no correction tables or EEPROM are written.
"""
import json
from pathlib import Path
import time
import numpy as np
from gnuradio import analog, blocks, gr, uhd
from diagnose_rf import summarize


def main():
    args = 'type=n3xx,addr=192.168.180.3,mgmt_addr=192.168.180.3,master_clock_rate=200e6'
    stream = uhd.stream_args(cpu_format='fc32', otw_format='sc16', channels=[0])
    rx = uhd.usrp_source(args, stream)
    tx = uhd.usrp_sink(args, stream, '')
    for block in (rx, tx):
        block.set_subdev_spec('A:0', 0)
        block.set_samp_rate(500000)
        block.set_center_freq(2450000000, 0)
        block.set_antenna('CAL', 0)
        block.set_gain(10, 0)
    tx.set_gain(40, 0)  # Internal CAL route, below the official utility's max-gain trial.
    tone = analog.sig_source_c(500000, analog.GR_COS_WAVE, 50000, 0.1)
    gate = blocks.multiply_const_cc(0)
    sink = blocks.vector_sink_c()
    tb = gr.top_block()
    tb.connect(tone, gate, tx)
    tb.connect(rx, sink)
    results = []
    print('N321 internal CAL only; no calibration data or firmware writes.', flush=True)
    tb.start()
    try:
        for enabled in (0,1,0):
            gate.set_k(enabled)
            time.sleep(0.25)
            sink.reset()
            start = time.monotonic()
            count0 = rx.nitems_written(0)
            txcount0 = tx.nitems_read(0)
            time.sleep(1)
            elapsed = time.monotonic() - start
            data = sink.data()
            row = dict(tx_enabled=enabled, rx_observed_sps=(rx.nitems_written(0)-count0)/elapsed,
                       tx_observed_sps=(tx.nitems_read(0)-txcount0)/elapsed,
                       measurement=summarize(data))
            np.asarray(data, dtype=np.complex64).tofile(Path(__file__).resolve().parent/f'n321_cal_tx{enabled}.c64')
            results.append(row)
            print(json.dumps(row), flush=True)
    finally:
        gate.set_k(0)
        tb.stop()
        tb.wait()
        # Restore external antenna selections with streams already stopped.
        tx.set_antenna('TX/RX', 0)
        rx.set_antenna('RX2', 0)
        (Path(__file__).resolve().parent/'diagnose_n321_internal_results.json').write_text(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
