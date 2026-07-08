from __future__ import annotations
from typing import Any
import config

def detect_failed_pressure(candles_5m:list[dict[str,Any]], box:dict[str,Any])->dict[str,Any]:
    recent=[c for c in candles_5m if c['ts']>=box['start_ts']] or candles_5m[-12:]
    high,low,width=box['box_high'],box['box_low'],max(box['box_width'],1e-12); edge=width*config.EDGE_ZONE_RATIO
    low_failed=[c for c in recent if c['low']<=low+edge and c['close']>low]
    high_failed=[c for c in recent if c['high']>=high-edge and c['close']<high]
    long_score=min(20,len(low_failed)*7+3); short_score=min(20,len(high_failed)*7+3)
    if long_score<8 and short_score<8: return {'ok':False,'reason_code':'NO_FAILED_PRESSURE','reason':'فشار ناموفق واضح در کف/سقف باکس دیده نشد'}
    direction='LONG' if long_score>=short_score else 'SHORT'
    return {'ok':True,'direction':direction,'score':max(long_score,short_score),'long_score':long_score,'short_score':short_score,'low_tests':len(low_failed),'high_tests':len(high_failed)}
