from __future__ import annotations
import json
from typing import Any
from database import get_conn
from utils import now_ms

def add(symbol, stage, reason_code, reason_text, side=None, score=None, details: dict[str,Any] | None = None) -> None:
    conn = get_conn()
    with conn: conn.execute('INSERT INTO rejections(ts_ms,symbol,side,stage,reason_code,reason_text,score,details_json) VALUES(?,?,?,?,?,?,?,?)',(now_ms(),symbol.upper() if symbol else None,side,stage,reason_code,reason_text,score,json.dumps(details or {},ensure_ascii=False)))
def list_rejections(limit: int = 50, symbol=None, reason=None, stage=None) -> list[dict]:
    sql='SELECT * FROM rejections WHERE 1=1'; params=[]
    if symbol: sql+=' AND symbol=?'; params.append(symbol.upper())
    if reason: sql+=' AND reason_code=?'; params.append(reason.upper())
    if stage: sql+=' AND stage=?'; params.append(stage)
    sql+=' ORDER BY id DESC LIMIT ?'; params.append(int(limit))
    return [dict(r) for r in get_conn().execute(sql,params).fetchall()]
