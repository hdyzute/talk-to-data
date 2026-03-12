"""
database.py — SQLite connection and query execution with self-correction loop support.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "sales.db"


def get_connection(db_path: str = str(DB_PATH)) -> sqlite3.Connection:
    """Return a SQLite connection (read-only mode for safety)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(sql: str, db_path: str = str(DB_PATH)) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Execute a SQL query and return (DataFrame, error_message).
    Returns (empty_df, error_str) on failure for self-correction loop.
    """
    try:
        conn = get_connection(db_path)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)