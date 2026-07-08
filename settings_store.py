from __future__ import annotations
import config
from database import get_conn
DEFAULTS = {'real_trading':'0','auto_signal':'1','margin_per_position':str(config.DEFAULT_MARGIN_PER_POSITION),'leverage':str(config.DEFAULT_LEVERAGE),'max_real_positions':str(config.DEFAULT_MAX_REAL_POSITIONS),'capital_limit':str(config.DEFAULT_CAPITAL_LIMIT),'fixed_fee':str(config.DEFAULT_FIXED_ROUND_TRIP_FEE),'min_net_profit':str(config.DEFAULT_MIN_NET_PROFIT)}

def ensure_defaults() -> None:
    conn = get_conn()
    with conn:
        for k,v in DEFAULTS.items(): conn.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)',(k,v))
def get(key: str, default: str | None = None) -> str:
    row = get_conn().execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone(); return str(row['value']) if row else DEFAULTS.get(key, default or '')
def set_value(key: str, value) -> None:
    if isinstance(value,bool): value='1' if value else '0'
    conn = get_conn()
    with conn: conn.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value)))
def get_bool(key: str) -> bool: return get(key,'0') in {'1','true','True','فعال','on','ON'}
def get_float(key: str) -> float:
    try: return float(get(key, DEFAULTS.get(key,'0')))
    except Exception: return 0.0
def get_int(key: str) -> int:
    try: return int(float(get(key, DEFAULTS.get(key,'0'))))
    except Exception: return 0
def snapshot() -> dict[str,str]: ensure_defaults(); return {k:get(k,v) for k,v in DEFAULTS.items()}
