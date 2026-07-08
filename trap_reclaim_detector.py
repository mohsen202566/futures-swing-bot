from __future__ import annotations
from typing import Any
import config

def detect_trap_reclaim(candles_5m:list[dict[str,Any]], box:dict[str,Any], preferred_direction:str|None=None)->dict[str,Any]:
    high,low,mid,width=box['box_high'],box['box_low'],box['box_mid'],max(box['box_width'],1e-12)
    opts=[]
    for c in candles_5m[-12:]:
        if c['low']<low and low<=c['close']<=high:
            depth=(low-c['low'])/width
            if depth<=config.MAX_SWEEP_DEPTH_RATIO:
                opts.append({'ok':True,'direction':'LONG','sweep_price':c['low'],'reclaim_close':c['close'],'sweep_ts':c['ts'],'score':min(25,14+(6 if c['close']>=mid else 3)+max(0,int((config.MAX_SWEEP_DEPTH_RATIO-depth)*8))),'reason':'sweep زیر باکس و برگشت داخل محدوده'})
        if c['high']>high and low<=c['close']<=high:
            depth=(c['high']-high)/width
            if depth<=config.MAX_SWEEP_DEPTH_RATIO:
                opts.append({'ok':True,'direction':'SHORT','sweep_price':c['high'],'reclaim_close':c['close'],'sweep_ts':c['ts'],'score':min(25,14+(6 if c['close']<=mid else 3)+max(0,int((config.MAX_SWEEP_DEPTH_RATIO-depth)*8))),'reason':'sweep بالای باکس و برگشت داخل محدوده'})
    if not opts: return {'ok':False,'reason_code':'NO_RECLAIM','reason':'sweep و برگشت معتبر داخل محدوده دیده نشد'}
    if preferred_direction:
        same=[o for o in opts if o['direction']==preferred_direction]
        if same: return same[-1]
    return max(opts,key=lambda x:x['score'])
