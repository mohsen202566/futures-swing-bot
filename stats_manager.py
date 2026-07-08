from __future__ import annotations
from database import get_conn
from utils import now_ms
DAY_MS=86400000

def _query(where='1=1', params=()):
    row=get_conn().execute(f"""SELECT COUNT(*) total,SUM(CASE WHEN result='TP' THEN 1 ELSE 0 END) tp,SUM(CASE WHEN result='SL' THEN 1 ELSE 0 END) sl,SUM(CASE WHEN status='OPEN' THEN 1 ELSE 0 END) open_count,SUM(COALESCE(raw_pnl,0)) raw_pnl,SUM(COALESCE(net_pnl,0)) net_pnl,SUM(CASE WHEN execution_status='REAL_FAILED' THEN 1 ELSE 0 END) real_failed FROM signals WHERE {where} AND status!='ARCHIVED'""",params).fetchone()
    d=dict(row) if row else {}; closed=int(d.get('tp') or 0)+int(d.get('sl') or 0); d['winrate']=(float(d.get('tp') or 0)/closed*100) if closed else 0.0; return d
def get_stats(days=None): return _query('created_at_ms>=?',(now_ms()-int(days)*DAY_MS,)) if days else _query()
def get_type_stats(t,days=None): return _query('signal_type=? AND created_at_ms>=?',(t,now_ms()-int(days)*DAY_MS)) if days else _query('signal_type=?',(t,))
def fmt(title,s): return f"{title}: تعداد: {int(s.get('total') or 0)} | TP: {int(s.get('tp') or 0)} | SL: {int(s.get('sl') or 0)} | باز: {int(s.get('open_count') or 0)} | وین‌ریت: {float(s.get('winrate') or 0):.1f}% | PnL خالص: {float(s.get('net_pnl') or 0):.2f} USDT"
def format_stats(days=30):
    all_s=get_stats(days); normal=get_type_stats('Normal',days); real=get_type_stats('Real',days); today=get_stats(1)
    return f"📊 آمار {days} روز اخیر\nسود/ضرر کل: {float(all_s.get('net_pnl') or 0):.2f} USDT\nسود/ضرر امروز: {float(today.get('net_pnl') or 0):.2f} USDT\n\n{fmt('📌 کل',all_s)}\n\n{fmt('📍 عادی',normal)}\n\n{fmt('💰 واقعی',real)}\nارسال واقعی ناموفق: {int(real.get('real_failed') or 0)}"
