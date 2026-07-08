from __future__ import annotations
from typing import Any
import log_store, signal_store, settings_store
from toobit_client import ToobitClient
from utils import now_ms
class ExecutionManager:
    def __init__(self,toobit:ToobitClient|None=None): self.toobit=toobit or ToobitClient()
    def execute_real(self,signal_id:int,sig:dict[str,Any])->dict[str,Any]:
        cid=f'FHT-{signal_id}-{now_ms()}'
        try:
            result=self.toobit.place_market_order(symbol=sig['symbol'],side=sig.get('order_side') or ('BUY' if sig['side']=='LONG' else 'SELL'),entry_price=float(sig['entry']),trade_amount_usdt=settings_store.get_float('margin_per_position'),leverage=settings_store.get_int('leverage'),tp_price=float(sig['tp']),sl_price=float(sig['sl']),client_order_id=cid)
            if result.get('opened'):
                signal_store.update_execution(signal_id,'REAL_OPEN',opened=True,order_id=result.get('order_id'),reason=result.get('reason'),opened_at_ms=now_ms()); log_store.add('REAL','execution_manager','پوزیشن Real تایید شد',sig['symbol'],result)
            else:
                signal_store.update_execution(signal_id,'REAL_FAILED',opened=False,order_id=result.get('order_id'),reason=result.get('reason')); log_store.add('ERROR','execution_manager','پوزیشن Real بعد از تایید 70 ثانیه‌ای باز نشد',sig['symbol'],result)
            return result
        except Exception as exc:
            reason=str(exc); signal_store.update_execution(signal_id,'REAL_FAILED',opened=False,reason=reason); log_store.add('ERROR','execution_manager',f'ارسال Real خطا داد: {reason}',sig['symbol']); return {'opened':False,'reason':reason}
