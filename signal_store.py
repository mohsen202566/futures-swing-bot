from __future__ import annotations
import json
from typing import Any
from database import get_conn
from utils import now_ms

def add_signal(sig: dict[str,Any], chat_id: int | None = None, message_id: int | None = None) -> int:
    conn = get_conn(); created = sig.get('created_at_ms') or now_ms()
    with conn:
        cur = conn.execute('''INSERT INTO signals(symbol,side,signal_type,entry,sl,tp,rr,score,raw_pnl_est,net_pnl_est,fee_est,notional_usdt,margin_usdt,leverage,telegram_chat_id,telegram_message_id,reasons_json,created_at_ms) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (sig['symbol'],sig['side'],sig.get('signal_type','Normal'),sig['entry'],sig['sl'],sig['tp'],sig['rr'],sig['score'],sig.get('raw_pnl_est',0),sig.get('net_pnl_est',0),sig.get('fee_est',0),sig.get('notional_usdt',0),sig.get('margin_usdt',0),sig.get('leverage',1),chat_id,message_id,json.dumps(sig.get('reasons',{}),ensure_ascii=False),created))
        return int(cur.lastrowid)
def update_message_id(signal_id:int, chat_id:int, message_id:int) -> None:
    with get_conn(): get_conn().execute('UPDATE signals SET telegram_chat_id=?,telegram_message_id=? WHERE id=?',(chat_id,message_id,signal_id))
def get_signal(signal_id:int) -> dict | None:
    row=get_conn().execute('SELECT * FROM signals WHERE id=?',(signal_id,)).fetchone(); return dict(row) if row else None
def get_open_signals() -> list[dict]: return [dict(r) for r in get_conn().execute("SELECT * FROM signals WHERE status='OPEN' ORDER BY id ASC").fetchall()]
def has_open_signal(symbol:str) -> bool: return get_conn().execute("SELECT 1 FROM signals WHERE symbol=? AND status='OPEN' LIMIT 1",(symbol.upper(),)).fetchone() is not None
def update_execution(signal_id:int, execution_status:str, opened:bool=False, order_id=None, reason=None, opened_at_ms=None) -> None:
    with get_conn(): get_conn().execute('UPDATE signals SET execution_status=?,real_opened=?,real_order_id=?,real_failed_reason=?,opened_at_ms=? WHERE id=?',(execution_status,1 if opened else 0,order_id,reason,opened_at_ms,signal_id))
def update_mfe_mae(signal_id:int, favorable_pct:float) -> None:
    row=get_signal(signal_id)
    if not row: return
    mfe=max(float(row.get('mfe_pct') or 0),favorable_pct); mae=min(float(row.get('mae_pct') or 0),favorable_pct)
    with get_conn(): get_conn().execute('UPDATE signals SET mfe_pct=?,mae_pct=? WHERE id=?',(mfe,mae,signal_id))
def close_signal(signal_id:int, result:str, exit_price:float, raw_pnl:float, net_pnl:float, close_reason:str) -> None:
    with get_conn(): get_conn().execute("UPDATE signals SET status='CLOSED',result=?,exit_price=?,raw_pnl=?,net_pnl=?,close_reason=?,closed_at_ms=? WHERE id=?",(result,exit_price,raw_pnl,net_pnl,close_reason,now_ms(),signal_id))
def count_real_open() -> int:
    row=get_conn().execute("SELECT COUNT(*) AS c FROM signals WHERE status='OPEN' AND signal_type='Real' AND real_opened=1").fetchone(); return int(row['c'] if row else 0)
def reset_stats_only() -> None:
    with get_conn(): get_conn().execute("UPDATE signals SET status='ARCHIVED' WHERE status='CLOSED'")
