from __future__ import annotations

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

_ENV_KEYS = [
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "OWNER_ID",
    "TOOBIT_API_KEY", "TOOBIT_API_SECRET",
    "DEFAULT_TRADE_ENABLED", "DEFAULT_TRADE_DOLLAR", "DEFAULT_LEVERAGE", "DEFAULT_MAX_POSITIONS",
    "ROUND_TRIP_FEE_USDT", "BOT_NAME", "BOT_DATA_DIR", "BOT_DB_PATH", "BOT_LOG_FILE",
    "OKX_BASE_URL", "TOOBIT_BASE_URL", "REQUEST_TIMEOUT", "RECV_WINDOW",
    "SCAN_INTERVAL_SECONDS", "MONITOR_INTERVAL_SECONDS", "BOT_RR",
    "DEFAULT_MARGIN_PER_POSITION", "DEFAULT_MAX_REAL_POSITIONS", "DEFAULT_CAPITAL_LIMIT",
    "DEFAULT_FIXED_ROUND_TRIP_FEE", "DEFAULT_MIN_NET_PROFIT", "DEFAULT_MARGIN_TYPE",
    "TOOBIT_VERIFY_AFTER_ERROR_SECONDS",
    "BOX_LOOKBACK_MIN_CANDLES", "BOX_LOOKBACK_MAX_CANDLES", "MIN_BOX_WIDTH_PCT",
    "MAX_BOX_WIDTH_PCT", "MAX_NOISY_WICK_RATIO", "EDGE_ZONE_RATIO", "MAX_SWEEP_DEPTH_RATIO",
    "MIN_SL_PCT", "MAX_SL_PCT", "SL_BUFFER_PCT", "MAX_LONG_ENTRY_POS_IN_BOX",
    "MIN_SHORT_ENTRY_POS_IN_BOX", "MIN_SIGNAL_SCORE", "STRONG_SIGNAL_SCORE",
    "BTC_ETH_DANGER_MOVE_PCT", "BTC_ETH_GUARD_CANDLES",
    "TOOBIT_PATH_BALANCE", "TOOBIT_PATH_POSITIONS", "TOOBIT_PATH_OPEN_ORDERS",
    "TOOBIT_PATH_MARGIN_MODE", "TOOBIT_PATH_LEVERAGE", "TOOBIT_PATH_POSITION_SETTINGS",
    "TOOBIT_PATH_ORDER", "TOOBIT_PATH_MARK_PRICE", "TOOBIT_PATH_EXCHANGE_INFO",
    "TOOBIT_PATH_HISTORY_POSITIONS", "TOOBIT_PATH_ORDER_HISTORY", "TOOBIT_PATH_ORDER_HISTORY_ALT",
    "TOOBIT_PATH_TODAY_PNL", "TOOBIT_PATH_CLOSE_ORDER", "TOOBIT_PARAM_TP", "TOOBIT_PARAM_SL",
]


def _strip_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.strip()


def _load_env_file() -> None:
    """Load root env files without requiring python-dotenv.

    Supports normal KEY=VALUE lines and also the accidentally-concatenated form:
    KEY=valueNEXT_KEY=value2
    OS environment variables always win over file values.
    """
    candidates = [BASE_DIR / ".env", BASE_DIR / "env", BASE_DIR / "config.env", BASE_DIR / "bot.env"]
    keys_alt = "|".join(sorted((re.escape(k) for k in _ENV_KEYS), key=len, reverse=True))
    concat_pattern = re.compile(rf"\b({keys_alt})=(.*?)(?=\b(?:{keys_alt})=|$)", re.S)

    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # First parse robust known-key chunks. This also handles ordinary newline files.
        for match in concat_pattern.finditer(text):
            key = match.group(1)
            value = _strip_env_value(match.group(2).split("\n", 1)[0] if "\n" in match.group(2) else match.group(2))
            if key and value and key not in os.environ:
                os.environ[key] = value
        # Then parse ordinary lines for any extra key.
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lstrip("export ").strip()
            value = _strip_env_value(value)
            if key and value and key not in os.environ:
                os.environ[key] = value


_load_env_file()


def _env_str(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return str(value)
    return default


def _env_int(*names: str, default: int = 0) -> int:
    value = _env_str(*names, default=str(default))
    try:
        return int(float(value))
    except Exception:
        return default


def _env_float(*names: str, default: float = 0.0) -> float:
    value = _env_str(*names, default=str(default))
    try:
        return float(value)
    except Exception:
        return default


def _env_bool(*names: str, default: bool = False) -> bool:
    value = _env_str(*names, default="1" if default else "0").strip().lower()
    return value in {"1", "true", "yes", "on", "فعال"}


BOT_NAME = _env_str("BOT_NAME", default="Futures Hunt Trap Bot")
BOT_DATA_DIR = Path(_env_str("BOT_DATA_DIR", default=str(BASE_DIR / "data")))
if not BOT_DATA_DIR.is_absolute():
    BOT_DATA_DIR = BASE_DIR / BOT_DATA_DIR
BOT_DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = _env_str("BOT_DB_PATH", default=str(BOT_DATA_DIR / "futures_hunt_trap.sqlite3"))
LOG_FILE = _env_str("BOT_LOG_FILE", default=str(BOT_DATA_DIR / "futures_hunt_trap.log"))

TELEGRAM_BOT_TOKEN = _env_str("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _env_int("TELEGRAM_CHAT_ID", default=0)
OWNER_ID = _env_int("OWNER_ID", default=TELEGRAM_CHAT_ID)

REQUEST_TIMEOUT = _env_int("REQUEST_TIMEOUT", default=15)
SCAN_INTERVAL_SECONDS = _env_int("SCAN_INTERVAL_SECONDS", default=300)
MONITOR_INTERVAL_SECONDS = _env_int("MONITOR_INTERVAL_SECONDS", default=20)
RR = _env_float("BOT_RR", default=1.5)

BOX_LOOKBACK_MIN_CANDLES = _env_int("BOX_LOOKBACK_MIN_CANDLES", default=3)
BOX_LOOKBACK_MAX_CANDLES = _env_int("BOX_LOOKBACK_MAX_CANDLES", default=8)
MIN_BOX_WIDTH_PCT = _env_float("MIN_BOX_WIDTH_PCT", default=0.12)
MAX_BOX_WIDTH_PCT = _env_float("MAX_BOX_WIDTH_PCT", default=1.20)
MAX_NOISY_WICK_RATIO = _env_float("MAX_NOISY_WICK_RATIO", default=0.72)
EDGE_ZONE_RATIO = _env_float("EDGE_ZONE_RATIO", default=0.22)
MAX_SWEEP_DEPTH_RATIO = _env_float("MAX_SWEEP_DEPTH_RATIO", default=0.55)
MIN_SL_PCT = _env_float("MIN_SL_PCT", default=0.15)
MAX_SL_PCT = _env_float("MAX_SL_PCT", default=1.20)
SL_BUFFER_PCT = _env_float("SL_BUFFER_PCT", default=0.03)
MAX_LONG_ENTRY_POS_IN_BOX = _env_float("MAX_LONG_ENTRY_POS_IN_BOX", default=0.72)
MIN_SHORT_ENTRY_POS_IN_BOX = _env_float("MIN_SHORT_ENTRY_POS_IN_BOX", default=0.28)
MIN_SIGNAL_SCORE = _env_int("MIN_SIGNAL_SCORE", default=75)
STRONG_SIGNAL_SCORE = _env_int("STRONG_SIGNAL_SCORE", default=85)
BTC_ETH_DANGER_MOVE_PCT = _env_float("BTC_ETH_DANGER_MOVE_PCT", default=0.65)
BTC_ETH_GUARD_CANDLES = _env_int("BTC_ETH_GUARD_CANDLES", default=4)

DEFAULT_REAL_TRADING = _env_bool("DEFAULT_TRADE_ENABLED", default=False)
DEFAULT_AUTO_SIGNAL = True
DEFAULT_MARGIN_PER_POSITION = _env_float("DEFAULT_TRADE_DOLLAR", "DEFAULT_MARGIN_PER_POSITION", default=10.0)
DEFAULT_LEVERAGE = _env_int("DEFAULT_LEVERAGE", default=10)
DEFAULT_MAX_REAL_POSITIONS = _env_int("DEFAULT_MAX_POSITIONS", "DEFAULT_MAX_REAL_POSITIONS", default=3)
DEFAULT_CAPITAL_LIMIT = _env_float("DEFAULT_CAPITAL_LIMIT", default=100.0)
DEFAULT_FIXED_ROUND_TRIP_FEE = _env_float("ROUND_TRIP_FEE_USDT", "DEFAULT_FIXED_ROUND_TRIP_FEE", default=0.05)
DEFAULT_MIN_NET_PROFIT = _env_float("DEFAULT_MIN_NET_PROFIT", default=0.01)
DEFAULT_MARGIN_TYPE = _env_str("DEFAULT_MARGIN_TYPE", default="ISOLATED")

OKX_BASE_URL = _env_str("OKX_BASE_URL", default="https://www.okx.com")
TOOBIT_BASE_URL = _env_str("TOOBIT_BASE_URL", default="https://api.toobit.com")
TOOBIT_API_KEY = _env_str("TOOBIT_API_KEY")
TOOBIT_API_SECRET = _env_str("TOOBIT_API_SECRET")
RECV_WINDOW = _env_int("RECV_WINDOW", default=5000)
TOOBIT_VERIFY_AFTER_ERROR_SECONDS = _env_int("TOOBIT_VERIFY_AFTER_ERROR_SECONDS", default=70)

TOOBIT_PATH_BALANCE = _env_str("TOOBIT_PATH_BALANCE", default="/api/v1/futures/balance")
TOOBIT_PATH_POSITIONS = _env_str("TOOBIT_PATH_POSITIONS", default="/api/v1/futures/positions")
TOOBIT_PATH_OPEN_ORDERS = _env_str("TOOBIT_PATH_OPEN_ORDERS", default="/api/v1/futures/openOrders")
TOOBIT_PATH_MARGIN_MODE = _env_str("TOOBIT_PATH_MARGIN_MODE", default="/api/v1/futures/marginType")
TOOBIT_PATH_LEVERAGE = _env_str("TOOBIT_PATH_LEVERAGE", default="/api/v1/futures/leverage")
TOOBIT_PATH_POSITION_SETTINGS = _env_str("TOOBIT_PATH_POSITION_SETTINGS", default="/api/v1/futures/accountLeverage")
TOOBIT_PATH_ORDER = _env_str("TOOBIT_PATH_ORDER", default="/api/v1/futures/order")
TOOBIT_PATH_MARK_PRICE = _env_str("TOOBIT_PATH_MARK_PRICE", default="/api/v1/futures/markPrice")
TOOBIT_PATH_EXCHANGE_INFO = _env_str("TOOBIT_PATH_EXCHANGE_INFO", default="/api/v1/futures/exchangeInfo")
TOOBIT_PATH_HISTORY_POSITIONS = _env_str("TOOBIT_PATH_HISTORY_POSITIONS", default="/api/v1/futures/historyPositions")
TOOBIT_PATH_ORDER_HISTORY = _env_str("TOOBIT_PATH_ORDER_HISTORY", default="/api/v1/futures/historyOrders")
TOOBIT_PATH_ORDER_HISTORY_ALT = _env_str("TOOBIT_PATH_ORDER_HISTORY_ALT", default="/api/v1/futures/order/history")
TOOBIT_PATH_TODAY_PNL = _env_str("TOOBIT_PATH_TODAY_PNL", default="/api/v1/futures/todayPnl")
TOOBIT_PATH_CLOSE_ORDER = _env_str("TOOBIT_PATH_CLOSE_ORDER", default=TOOBIT_PATH_ORDER)
TOOBIT_PARAM_TP = _env_str("TOOBIT_PARAM_TP", default="takeProfit")
TOOBIT_PARAM_SL = _env_str("TOOBIT_PARAM_SL", default="stopLoss")
