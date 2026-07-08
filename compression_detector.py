from __future__ import annotations
from typing import Any
import config

def _wick_ratio(c:dict[str,Any])->float:
    rng=max(c['high']-c['low'],1e-12); body=abs(c['close']-c['open']); return max(0,min(1,(rng-body)/rng))
def detect_compression(candles_15m:list[dict[str,Any]])->dict[str,Any]:
    if len(candles_15m) < config.BOX_LOOKBACK_MIN_CANDLES: return {'ok':False,'reason_code':'DATA_ERROR','reason':'کندل 15M کافی نیست'}
    best=None
    maxn=min(config.BOX_LOOKBACK_MAX_CANDLES,len(candles_15m))
    for n in range(config.BOX_LOOKBACK_MIN_CANDLES,maxn+1):
        w=candles_15m[-n:]; high=max(c['high'] for c in w); low=min(c['low'] for c in w); mid=(high+low)/2
        width_pct=(high-low)/mid*100 if mid else 999; avg_wick=sum(_wick_ratio(c) for c in w)/len(w)
        if width_pct<config.MIN_BOX_WIDTH_PCT or width_pct>config.MAX_BOX_WIDTH_PCT or avg_wick>config.MAX_NOISY_WICK_RATIO: continue
        score=max(10,min(20,20-int((width_pct/config.MAX_BOX_WIDTH_PCT)*8)-int(avg_wick*5)))
        cand={'ok':True,'score':score,'box_high':high,'box_low':low,'box_mid':mid,'box_width':high-low,'box_width_pct':width_pct,'candles':n,'start_ts':w[0]['ts'],'end_ts':w[-1]['ts'],'avg_wick_ratio':avg_wick}
        if best is None or cand['box_width_pct'] < best['box_width_pct']: best=cand
    return best or {'ok':False,'reason_code':'NO_COMPRESSION','reason':'فشردگی سالم پیدا نشد یا باکس خیلی بزرگ/نویزی بود'}
