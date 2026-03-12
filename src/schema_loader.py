"""
schema_loader.py — Extract full schema from SQLite and format it for LLM prompts.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List

DB_PATH = Path(__file__).parent.parent / "data" / "sales.db"


def get_schema(db_path: str = str(DB_PATH)) -> Dict[str, List[dict]]:
    """
    Return schema as dict: { table_name: [ {name, type, pk, notnull} ] }
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cur.fetchall()]

    schema = {}
    for table in tables:
        cur.execute(f"PRAGMA table_info({table});")
        cols = [
            {"name": row[1], "type": row[2], "notnull": bool(row[3]), "pk": bool(row[5])}
            for row in cur.fetchall()
        ]
        schema[table] = cols

    conn.close()
    return schema


def get_schema_prompt(db_path: str = str(DB_PATH)) -> str:
    """
    Format schema as a clean string to inject into LLM system prompt.
    Example output:
        Table: sales
          - sale_id (INTEGER) [PK]
          - customer_id (INTEGER)
          ...
    """
    schema = get_schema(db_path)
    lines = ["DATABASE SCHEMA (SQLite):"]
    for table, cols in schema.items():
        lines.append(f"\nTable: {table}")
        for col in cols:
            flags = []
            if col["pk"]:
                flags.append("PK")
            if col["notnull"]:
                flags.append("NOT NULL")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            lines.append(f"  - {col['name']} ({col['type']}){flag_str}")
    return "\n".join(lines)


def get_sample_rows(db_path: str = str(DB_PATH), n: int = 3) -> str:
    """Return sample rows per table to give LLM data context."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cur.fetchall()]

    lines = ["\nSAMPLE DATA:"]
    for table in tables:
        cur.execute(f"SELECT * FROM {table} LIMIT {n};")
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        lines.append(f"\n{table}: {col_names}")
        for row in rows:
            lines.append(f"  {list(row)}")
    conn.close()
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_schema_prompt())
    print(get_sample_rows())