from __future__ import annotations
import config
from utils import pct_change

def check_btc_eth_guard(okx_market, side:str)->dict:
    try:
        btc=okx_market.get_candles('BTCUSDT','5m',config.BTC_ETH_GUARD_CANDLES+1); eth=okx_market.get_candles('ETHUSDT','5m',config.BTC_ETH_GUARD_CANDLES+1)
        if len(btc)<2 or len(eth)<2: return {'ok':True,'score_adj':0,'reason':'دیتای BTC/ETH کافی نبود؛ رد نکردیم'}
        bm=pct_change(btc[0]['open'],btc[-1]['close']); em=pct_change(eth[0]['open'],eth[-1]['close']); d=config.BTC_ETH_DANGER_MOVE_PCT
        if side=='LONG' and bm<=-d and em<=-d: return {'ok':False,'reason_code':'BTC_ETH_DANGER','reason':'BTC و ETH همزمان دامپ شدید دارند','btc_move':bm,'eth_move':em}
        if side=='SHORT' and bm>=d and em>=d: return {'ok':False,'reason_code':'BTC_ETH_DANGER','reason':'BTC و ETH همزمان پامپ شدید دارند','btc_move':bm,'eth_move':em}
        adj=3 if ((side=='LONG' and bm>0 and em>0) or (side=='SHORT' and bm<0 and em<0)) else 0
        return {'ok':True,'score_adj':adj,'btc_move':bm,'eth_move':em,'reason':'خطر شدید BTC/ETH دیده نشد'}
    except Exception as exc:
        return {'ok':True,'score_adj':0,'reason':f'خطای گارد BTC/ETH؛ رد نکردیم: {exc}'}
