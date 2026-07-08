from __future__ import annotations
from typing import Any
from okx_monitor import OKXMonitor, pnl_for_signal
import signal_store
from toobit_client import ToobitClient
from utils import now_ms
class ResultMonitor:
    def __init__(self, okx_monitor:OKXMonitor, toobit:ToobitClient|None=None): self.okx_monitor=okx_monitor; self.toobit=toobit or ToobitClient()
    def check_signal(self,row:dict[str,Any])->dict[str,Any]|None:
        if row['signal_type']=='Real' and int(row.get('real_opened') or 0)==1: return self._check_real(row)
        return self.okx_monitor.check_normal_signal(row)
    def _check_real(self,row:dict[str,Any])->dict[str,Any]|None:
        symbol=row['symbol']; side='BUY' if row['side']=='LONG' else 'SELL'
        try:
            if self.toobit.get_open_position(symbol,side): return None
            start=int(row.get('opened_at_ms') or row.get('created_at_ms') or now_ms()); realized=self.toobit.find_realized_result(symbol,side,start_ms=start)
            if not realized: return None
            pnl=float(realized.get('pnl') or 0); exit_price=float(realized.get('close_price') or (row['tp'] if pnl>=0 else row['sl'])); result='TP' if pnl>=0 else 'SL'
            raw,net=pnl_for_signal(row,exit_price); net=pnl
            signal_store.close_signal(int(row['id']),result,exit_price,raw,net,'Toobit real position closed.')
            return {'result':result,'exit_price':exit_price,'raw_pnl':raw,'net_pnl':net,'close_reason':'Toobit real position closed.'}
        except Exception: return None
