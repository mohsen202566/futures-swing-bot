from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import config

_LOCK = threading.RLock()
_CONN: sqlite3.Connection | None = None

SIGNAL_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "symbol": "TEXT",
    "side": "TEXT",
    "signal_type": "TEXT DEFAULT 'Normal'",
    "entry": "REAL",
    "sl": "REAL",
    "tp": "REAL",
    "rr": "REAL",
    "score": "INTEGER",
    "raw_pnl_est": "REAL DEFAULT 0",
    "net_pnl_est": "REAL DEFAULT 0",
    "fee_est": "REAL DEFAULT 0",
    "notional_usdt": "REAL DEFAULT 0",
    "margin_usdt": "REAL DEFAULT 0",
    "leverage": "INTEGER DEFAULT 1",
    "status": "TEXT DEFAULT 'OPEN'",
    "result": "TEXT",
    "exit_price": "REAL",
    "raw_pnl": "REAL DEFAULT 0",
    "net_pnl": "REAL DEFAULT 0",
    "mfe_pct": "REAL DEFAULT 0",
    "mae_pct": "REAL DEFAULT 0",
    "close_reason": "TEXT",
    "execution_status": "TEXT DEFAULT 'NONE'",
    "real_order_id": "TEXT",
    "real_opened": "INTEGER DEFAULT 0",
    "real_failed_reason": "TEXT",
    "telegram_chat_id": "INTEGER",
    "telegram_message_id": "INTEGER",
    "reasons_json": "TEXT DEFAULT '{}'",
    "created_at_ms": "INTEGER",
    "opened_at_ms": "INTEGER",
    "closed_at_ms": "INTEGER",
}

REJECTION_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "ts_ms": "INTEGER",
    "symbol": "TEXT",
    "side": "TEXT",
    "stage": "TEXT",
    "reason_code": "TEXT",
    "reason_text": "TEXT",
    "score": "INTEGER",
    "details_json": "TEXT DEFAULT '{}'",
}

LOG_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "ts_ms": "INTEGER",
    "level": "TEXT",
    "module": "TEXT",
    "symbol": "TEXT",
    "message": "TEXT",
    "data_json": "TEXT DEFAULT '{}'",
}


def get_conn() -> sqlite3.Connection:
    global _CONN
    with _LOCK:
        if _CONN is None:
            Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
            _CONN = sqlite3.connect(config.DB_PATH, check_same_thread=False)
            _CONN.row_factory = sqlite3.Row
            _CONN.execute("PRAGMA journal_mode=WAL")
        return _CONN


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _create_table_if_missing(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    if _table_exists(conn, table):
        return
    cols = ", ".join(f"{name} {definition}" for name, definition in columns.items())
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table}({cols})")


def _add_missing_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = _existing_columns(conn, table)
    for name, definition in columns.items():
        if name in existing or name == "id":
            continue
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    _create_table_if_missing(conn, "signals", SIGNAL_COLUMNS)
    _add_missing_columns(conn, "signals", SIGNAL_COLUMNS)

    _create_table_if_missing(conn, "rejections", REJECTION_COLUMNS)
    _add_missing_columns(conn, "rejections", REJECTION_COLUMNS)

    _create_table_if_missing(conn, "logs", LOG_COLUMNS)
    _add_missing_columns(conn, "logs", LOG_COLUMNS)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol_status ON signals(symbol, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at_ms)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rejections_ts ON rejections(ts_ms)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts_ms)")


def init_db() -> None:
    conn = get_conn()
    with conn:
        _ensure_schema(conn)
