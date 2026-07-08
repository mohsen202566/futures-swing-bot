from __future__ import annotations
from typing import Any
import config
import rejection_store, settings_store
from compression_detector import detect_compression
from pressure_detector import detect_failed_pressure
from trap_reclaim_detector import detect_trap_reclaim
from btc_eth_guard import check_btc_eth_guard
from entry_scorer import entry_location_score, risk_score, total_score
from utils import now_ms
class SignalEngine:
    def __init__(self, okx_market): self.okx=okx_market
    def evaluate(self, symbol:str)->dict[str,Any]|None:
        symbol=symbol.upper()
        try:
            c15=self.okx.get_candles(symbol,'15m',80); c5=self.okx.get_candles(symbol,'5m',80)
            if len(c15)<8 or len(c5)<20:
                rejection_store.add(symbol,'data','DATA_ERROR','کندل کافی از OKX دریافت نشد'); return None
        except Exception as exc:
            rejection_store.add(symbol,'data','DATA_ERROR',f'خطای دریافت دیتای OKX: {exc}'); return None
        comp=detect_compression(c15)
        if not comp.get('ok'):
            rejection_store.add(symbol,'compression',comp.get('reason_code','NO_COMPRESSION'),comp.get('reason','فشردگی رد شد'),details=comp); return None
        pressure=detect_failed_pressure(c5,comp)
        if not pressure.get('ok'):
            rejection_store.add(symbol,'pressure',pressure.get('reason_code','NO_FAILED_PRESSURE'),pressure.get('reason','فشار ناموفق رد شد'),details={'box':comp,**pressure}); return None
        trap=detect_trap_reclaim(c5,comp,pressure.get('direction'))
        if not trap.get('ok'):
            rejection_store.add(symbol,'trap_reclaim',trap.get('reason_code','NO_RECLAIM'),trap.get('reason','تله/برگشت رد شد'),side=pressure.get('direction'),details={'box':comp,'pressure':pressure,**trap}); return None
        side=trap['direction']; entry=float(c5[-1]['close'])
        loc,loc_err=entry_location_score(side,entry,comp)
        if loc_err:
            rejection_store.add(symbol,'entry',loc_err,'جای ورود بد یا دیر است؛ ورود باید قبل از شکست اصلی و داخل محدوده باشد',side=side,details={'entry':entry,'box':comp}); return None
        buffer=max(entry*config.SL_BUFFER_PCT/100, comp['box_width']*0.04)
        if side=='LONG':
            sl=float(trap['sweep_price']-buffer); risk=entry-sl; tp=entry+risk*config.RR; order_side='BUY'
        else:
            sl=float(trap['sweep_price']+buffer); risk=sl-entry; tp=entry-risk*config.RR; order_side='SELL'
        margin=settings_store.get_float('margin_per_position'); lev=settings_store.get_int('leverage'); fee=settings_store.get_float('fixed_fee'); min_net=settings_store.get_float('min_net_profit')
        notional=margin*lev; raw=abs(tp-entry)/entry*notional if entry else 0; net=raw-fee
        rs, rerr, risk_pct = risk_score(entry,sl,tp,net,min_net)
        if rerr:
            rejection_store.add(symbol,'risk',rerr,'SL/TP بعد از کارمزد ارزشمند نیست یا استاپ غیرمنطقی است',side=side,details={'entry':entry,'sl':sl,'tp':tp,'risk_pct':risk_pct,'net_pnl_est':net}); return None
        guard=check_btc_eth_guard(self.okx,side)
        if not guard.get('ok'):
            rejection_store.add(symbol,'btc_eth_guard',guard.get('reason_code','BTC_ETH_DANGER'),guard.get('reason','BTC/ETH خطرناک است'),side=side,details=guard); return None
        score=total_score(comp,pressure,trap,loc,rs,int(guard.get('score_adj',0)))
        if score<config.MIN_SIGNAL_SCORE:
            rejection_store.add(symbol,'score','LOW_SCORE',f'امتیاز سیگنال پایین است: {score}',side=side,score=score,details={'compression':comp,'pressure':pressure,'trap':trap,'guard':guard}); return None
        return {'symbol':symbol,'side':side,'order_side':order_side,'entry':round(entry,10),'sl':round(sl,10),'tp':round(tp,10),'rr':config.RR,'score':score,'strength':'قوی' if score>=config.STRONG_SIGNAL_SCORE else 'عادی','raw_pnl_est':raw,'net_pnl_est':net,'fee_est':fee,'notional_usdt':notional,'margin_usdt':margin,'leverage':lev,'created_at_ms':now_ms(),'reasons':{'compression':comp,'pressure':pressure,'trap':trap,'entry_location_score':loc,'risk_score':rs,'btc_eth_guard':guard}}
