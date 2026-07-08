from __future__ import annotations
import sqlite3, threading
from pathlib import Path
import config
_LOCK = threading.RLock(); _CONN: sqlite3.Connection | None = None

def get_conn() -> sqlite3.Connection:
    global _CONN
    with _LOCK:
        if _CONN is None:
            Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
            _CONN = sqlite3.connect(config.DB_PATH, check_same_thread=False)
            _CONN.row_factory = sqlite3.Row
            _CONN.execute("PRAGMA journal_mode=WAL")
        return _CONN

def init_db() -> None:
    conn = get_conn()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS signals(
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, side TEXT, signal_type TEXT DEFAULT 'Normal',
            entry REAL, sl REAL, tp REAL, rr REAL, score INTEGER, raw_pnl_est REAL DEFAULT 0, net_pnl_est REAL DEFAULT 0,
            fee_est REAL DEFAULT 0, notional_usdt REAL DEFAULT 0, margin_usdt REAL DEFAULT 0, leverage INTEGER DEFAULT 1,
            status TEXT DEFAULT 'OPEN', result TEXT, exit_price REAL, raw_pnl REAL DEFAULT 0, net_pnl REAL DEFAULT 0,
            mfe_pct REAL DEFAULT 0, mae_pct REAL DEFAULT 0, close_reason TEXT, execution_status TEXT DEFAULT 'NONE',
            real_order_id TEXT, real_opened INTEGER DEFAULT 0, real_failed_reason TEXT,
            telegram_chat_id INTEGER, telegram_message_id INTEGER, reasons_json TEXT DEFAULT '{}', created_at_ms INTEGER,
            opened_at_ms INTEGER, closed_at_ms INTEGER);
        CREATE INDEX IF NOT EXISTS idx_signals_symbol_status ON signals(symbol,status);
        CREATE TABLE IF NOT EXISTS rejections(id INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER, symbol TEXT, side TEXT, stage TEXT,
            reason_code TEXT, reason_text TEXT, score INTEGER, details_json TEXT DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts_ms INTEGER, level TEXT, module TEXT, symbol TEXT, message TEXT, data_json TEXT DEFAULT '{}');
        """)
