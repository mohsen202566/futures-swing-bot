from __future__ import annotations
from typing import Any
import signal_store, settings_store

def favorable_pct(row:dict[str,Any], price:float)->float:
    e=float(row['entry'])
    return ((price-e)/e*100 if row['side']=='LONG' else (e-price)/e*100) if e else 0

def pnl_for_signal(row:dict[str,Any], exit_price:float)->tuple[float,float]:
    e=float(row['entry']); notional=float(row.get('notional_usdt') or (float(row.get('margin_usdt') or 0)*float(row.get('leverage') or 1)))
    raw=((exit_price-e)/e*notional if row['side']=='LONG' else (e-exit_price)/e*notional) if e else 0
    fee=float(row.get('fee_est') or settings_store.get_float('fixed_fee')); return raw, raw-fee
class OKXMonitor:
    def __init__(self, okx_market): self.okx=okx_market
    def check_normal_signal(self,row:dict[str,Any])->dict[str,Any]|None:
        price=self.okx.get_last_price(row['symbol']); signal_store.update_mfe_mae(int(row['id']),favorable_pct(row,price))
        side=row['side']; tp=float(row['tp']); sl=float(row['sl']); result=None
        if side=='LONG':
            if price>=tp: result='TP'; price=tp
            elif price<=sl: result='SL'; price=sl
        else:
            if price<=tp: result='TP'; price=tp
            elif price>=sl: result='SL'; price=sl
        if not result: return None
        raw,net=pnl_for_signal(row,price); signal_store.close_signal(int(row['id']),result,price,raw,net,'OKX monitor hit TP/SL.')
        return {'result':result,'exit_price':price,'raw_pnl':raw,'net_pnl':net,'close_reason':'OKX monitor hit TP/SL.'}
