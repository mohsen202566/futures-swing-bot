from __future__ import annotations
import settings_store, signal_store
from toobit_client import ToobitClient
class SlotManager:
    def __init__(self, toobit:ToobitClient|None=None): self.toobit=toobit or ToobitClient()
    def max_positions(self): return settings_store.get_int('max_real_positions')
    def real_open_count(self): return signal_store.count_real_open()
    def free_slots(self): return max(0,self.max_positions()-self.real_open_count())
    def can_open_real(self,symbol:str):
        if self.free_slots()<=0: return False,'اسلات Real پر است'
        if signal_store.has_open_signal(symbol): return False,'برای این ارز سیگنال باز وجود دارد'
        try:
            if self.toobit.has_open_position(symbol): return False,'برای این ارز در Toobit پوزیشن باز وجود دارد'
            if self.toobit.has_open_order(symbol): return False,'برای این ارز در Toobit سفارش باز وجود دارد'
        except Exception as exc: return False,f'چک Toobit ناموفق بود: {exc}'
        return True,'OK'
