from __future__ import annotations
import config

def entry_location_score(side:str, entry:float, box:dict)->tuple[int,str|None]:
    high,low,width=box['box_high'],box['box_low'],max(box['box_width'],1e-12); pos=(entry-low)/width
    if entry<=low or entry>=high: return 0,'ENTRY_OUTSIDE_BOX'
    if side=='LONG':
        if pos>config.MAX_LONG_ENTRY_POS_IN_BOX: return 0,'LATE_ENTRY'
        score=int(20*(1-max(0,pos-0.25)/max(0.01,config.MAX_LONG_ENTRY_POS_IN_BOX-0.25)))
    else:
        if pos<config.MIN_SHORT_ENTRY_POS_IN_BOX: return 0,'LATE_ENTRY'
        score=int(20*(1-max(0,0.75-pos)/max(0.01,0.75-config.MIN_SHORT_ENTRY_POS_IN_BOX)))
    return max(8,min(20,score)),None
def risk_score(entry:float, sl:float, tp:float, net_profit:float, min_net_profit:float)->tuple[int,str|None,float]:
    risk_pct=abs(entry-sl)/entry*100 if entry else 999
    if risk_pct<config.MIN_SL_PCT or risk_pct>config.MAX_SL_PCT: return 0,'BAD_SL',risk_pct
    if net_profit<min_net_profit: return 0,'BAD_RR',risk_pct
    score=15-(3 if risk_pct>0.9 else 0)-(2 if risk_pct<0.3 else 0)
    return max(7,score),None,risk_pct
def total_score(compression,pressure,trap,loc,risk,btc_adj=0)->int:
    return int(min(100,max(0,int(compression.get('score',0))+int(pressure.get('score',0))+int(trap.get('score',0))+int(loc)+int(risk)+int(btc_adj))))
