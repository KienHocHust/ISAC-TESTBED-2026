#!/usr/bin/env python3
"""Offline decoder sweep for captured IQ; no USRP and no RF transmission.

For diagnosis only: clone the installed GNU Radio ofdm_rx class in a private
namespace and change its sync threshold, without editing installed modules.
"""
import argparse
import ast
import inspect
import json
from pathlib import Path
import sys
import time
from gnuradio import blocks, digital, gr
from check_rx import expected_payload, settings


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('file',type=Path)
    ap.add_argument('--sample-rate',type=int,default=500000)
    args=ap.parse_args()
    cfg=settings();expected=expected_payload();fft_len=ast.literal_eval(cfg['fft_len']['value'])
    p=cfg['digital_ofdm_rx_0']
    def expr(key):
        return eval(p[key],{'__builtins__':{},'list':list,'range':range},{'fft_len':fft_len})
    params=dict(fft_len=fft_len,cp_len=expr('cp_len'),occupied_carriers=expr('occupied_carriers'),
                pilot_carriers=expr('pilot_carriers'),pilot_symbols=expr('pilot_symbols'),
                sync_word1=expr('sync_word1'),sync_word2=expr('sync_word2'),
                bps_header=1,bps_payload=2,scramble_bits=expr('scramble_bits'),debug_log=False,
                packet_length_tag_key='rx_len',frame_length_tag_key='frame_rx_len')
    source_code=inspect.getsource(digital.ofdm_rx)
    target='digital.ofdm_sync_sc_cfb(fft_len, cp_len, even_carriers)'
    assert target in source_code
    reports=[]
    for threshold in [0.9,0.7,0.5,0.3]:
        namespace=dict(vars(sys.modules[digital.ofdm_rx.__module__]))
        exec(source_code.replace(target,f'digital.ofdm_sync_sc_cfb(fft_len, cp_len, even_carriers, {threshold})'),namespace)
        modem=namespace['ofdm_rx'](**params)
        tb=gr.top_block();src=blocks.file_source(gr.sizeof_gr_complex,str(args.file.resolve()),False)
        # Decode an on-air section, excluding start/stop transients.
        src.seek(4*args.sample_rate,0)
        head=blocks.head(gr.sizeof_gr_complex,4*args.sample_rate)
        sink=blocks.vector_sink_b();tb.connect(src,head,modem,sink)
        tb.start();time.sleep(4);tb.stop();tb.wait()
        data=bytes(sink.data());n,partial=divmod(len(data),len(expected))
        matched=sum(data[i:i+len(expected)]==expected for i in range(0,n*len(expected),len(expected)))
        row=dict(threshold=threshold,bytes=len(data),matched=matched,unexpected=n-matched,partial=partial,
                 iq_consumed=head.nitems_written(0))
        print(json.dumps(row),flush=True);reports.append(row)
        if matched>=10 and matched==n and partial==0:break
    output=args.file.with_name(args.file.stem+'_decode.json');output.write_text(json.dumps(reports,indent=2))


if __name__=='__main__':main()
