from __future__ import annotations
import logging, time
from decimal import Decimal, ROUND_DOWN
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
import config
logger = logging.getLogger("futures_hunt_trap")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    sh = logging.StreamHandler(); sh.setFormatter(fmt); logger.addHandler(sh)
    try:
        Path(config.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(config.LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"); fh.setFormatter(fmt); logger.addHandler(fh)
    except Exception: pass

def now_ms() -> int: return int(time.time() * 1000)
def safe_float(v: Any, default: float = 0.0) -> float:
    try: return default if v in (None, "") else float(v)
    except Exception: return default
def safe_int(v: Any, default: int = 0) -> int:
    try: return default if v in (None, "") else int(float(v))
    except Exception: return default
def decimal_round_down(value: float | Decimal, step: str | float | None = None, digits: int = 8) -> str:
    d = Decimal(str(value))
    if step not in (None, "", 0, "0"):
        s = Decimal(str(step))
        if s > 0: return format(((d / s).to_integral_value(rounding=ROUND_DOWN) * s).normalize(), "f")
    q = Decimal("1") / (Decimal("10") ** digits)
    return format(d.quantize(q, rounding=ROUND_DOWN).normalize(), "f")
def extract_filter(info: dict[str, Any], filter_type: str) -> dict[str, Any]:
    for key in ("filters", "filter", "rules"):
        vals = info.get(key)
        if isinstance(vals, list):
            for item in vals:
                if isinstance(item, dict) and str(item.get("filterType") or item.get("type") or "").upper() == filter_type.upper(): return item
    return {}
def side_to_toobit_open(side: str) -> str:
    side = str(side).upper()
    if side in {"BUY", "LONG"}: return "BUY_OPEN"
    if side in {"SELL", "SHORT"}: return "SELL_OPEN"
    return side
def side_to_toobit_position(side: str | None) -> str:
    side = str(side or "").upper()
    if side in {"BUY", "LONG", "BUY_OPEN"}: return "LONG"
    if side in {"SELL", "SHORT", "SELL_OPEN"}: return "SHORT"
    return side or "LONG"
def toobit_symbol_candidates(s: str) -> list[str]:
    s = str(s).upper().replace("-", "").replace("_", "")
    out = [s]
    if s.endswith("USDT"):
        b = s[:-4]; out += [f"{b}-USDT", f"{b}_USDT", f"{b}USDT"]
    return list(dict.fromkeys(out))
def okx_inst_id(s: str) -> str:
    s = str(s).upper().replace("-", "").replace("_", "")
    return f"{s[:-4]}-USDT-SWAP" if s.endswith("USDT") else s
def pct_change(a: float, b: float) -> float: return ((b - a) / a * 100.0) if a else 0.0
