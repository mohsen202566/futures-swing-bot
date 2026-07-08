from __future__ import annotations
import json
from typing import Any
from database import get_conn
from utils import now_ms

def add(level: str, module: str, message: str, symbol: str | None = None, data: dict[str,Any] | None = None) -> None:
    conn = get_conn()
    with conn: conn.execute('INSERT INTO logs(ts_ms,level,module,symbol,message,data_json) VALUES(?,?,?,?,?,?)',(now_ms(),level.upper(),module,symbol,message,json.dumps(data or {},ensure_ascii=False)))
def list_logs(limit: int = 50, level: str | None = None, symbol: str | None = None) -> list[dict]:
    sql='SELECT * FROM logs WHERE 1=1'; params=[]
    if level: sql+=' AND level=?'; params.append(level.upper())
    if symbol: sql+=' AND symbol=?'; params.append(symbol.upper())
    sql+=' ORDER BY id DESC LIMIT ?'; params.append(int(limit))
    return [dict(r) for r in get_conn().execute(sql,params).fetchall()]
