from __future__ import annotations
from typing import Any
from okx_client import OKXClient
from utils import okx_inst_id, safe_float, safe_int
class OKXMarket:
    def __init__(self, client: OKXClient | None = None): self.client = client or OKXClient()
    def get_candles(self, symbol: str, bar: str = '5m', limit: int = 100) -> list[dict[str,Any]]:
        payload = self.client.get('/api/v5/market/candles', {'instId': okx_inst_id(symbol), 'bar': bar, 'limit': str(limit)})
        rows = payload.get('data', []) if isinstance(payload, dict) else []
        out=[]
        for r in rows:
            if not isinstance(r, list) or len(r) < 6: continue
            out.append({'ts':safe_int(r[0]),'open':safe_float(r[1]),'high':safe_float(r[2]),'low':safe_float(r[3]),'close':safe_float(r[4]),'volume':safe_float(r[5]),'confirm':str(r[8])=='1' if len(r)>8 else True})
        out.sort(key=lambda x:x['ts']); return out
    def get_last_price(self, symbol: str) -> float:
        payload = self.client.get('/api/v5/market/ticker', {'instId': okx_inst_id(symbol)})
        data = payload.get('data', []) if isinstance(payload, dict) else []
        if not data: raise RuntimeError(f'OKX ticker برای {symbol} خالی است')
        return safe_float(data[0].get('last') or data[0].get('markPx') or data[0].get('idxPx'))
