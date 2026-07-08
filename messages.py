from __future__ import annotations
from typing import Any

def format_signal(sig:dict[str,Any], signal_id:int, signal_type:str, execution_note:str='')->str:
    r=sig.get('reasons',{}); comp=r.get('compression',{}); pressure=r.get('pressure',{}); trap=r.get('trap',{})
    title='📊 سیگنال واقعی' if signal_type=='Real' else '📊 سیگنال عادی'
    return (f"{title}\n#{signal_id} | {sig['symbol']} | {sig['side']}\n\nEntry: {sig['entry']}\nSL: {sig['sl']}\nTP: {sig['tp']}\nRR: {sig['rr']}\nScore: {sig['score']} | قدرت: {sig.get('strength','عادی')}\n\nPnL خام تقریبی: {sig.get('raw_pnl_est',0):.2f} USDT\nPnL خالص تقریبی: {sig.get('net_pnl_est',0):.2f} USDT\nکارمزد رفت‌وبرگشت: {sig.get('fee_est',0):.2f} USDT\n\nدلیل:\n• فشردگی معتبر 15M: {comp.get('candles','-')} کندل | عرض {comp.get('box_width_pct',0):.2f}%\n• فشار ناموفق: {pressure.get('direction','-')} | امتیاز {pressure.get('score','-')}\n• تله/برگشت: {trap.get('reason','-')}\n• ورود قبل از شکست اصلی، SL پشت تله\n{execution_note}")

def format_result(row:dict[str,Any], result:dict[str,Any])->str:
    title='📊 نتیجه سیگنال واقعی' if row.get('signal_type')=='Real' else '📊 نتیجه سیگنال عادی'
    icon='✅ TP خورد' if result['result']=='TP' else '❌ SL خورد'
    created=int(row.get('created_at_ms') or 0); closed=int(row.get('closed_at_ms') or 0); duration='-'
    if created and closed:
        mins=max(0,(closed-created)//60000); duration=f'{mins//60} ساعت و {mins%60} دقیقه' if mins>=60 else f'{mins} دقیقه'
    return (f"{title}\n\n{icon}\n#{row['id']} | {row['symbol']} | {row['side']}\nEntry: {row['entry']}\nExit: {result['exit_price']}\n\nPnL خام: {result['raw_pnl']:.2f} USDT\nPnL خالص/واقعی: {result['net_pnl']:.2f} USDT\n\nMFE: {float(row.get('mfe_pct') or 0):.2f}% | MAE: {float(row.get('mae_pct') or 0):.2f}%\nمدت معامله: {duration}\nclose_reason: {result['close_reason']}")

def format_rejections(rows:list[dict[str,Any]])->str:
    if not rows: return 'لاگ ردی وجود ندارد.'
    lines=['📋 آخرین رد شدن‌ها']
    for i,r in enumerate(rows,1):
        lines += [f"\n{i}) {r.get('symbol') or '-'} | {r.get('side') or '-'}", f"مرحله: {r.get('stage')} | دلیل: {r.get('reason_code')}", str(r.get('reason_text') or '')]
    return '\n'.join(lines)
