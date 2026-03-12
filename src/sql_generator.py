"""
sql_generator.py — Schema-aware SQL generation with self-correction loop.
"""

import re
from src.llm import chat
from src.schema_loader import get_schema_prompt, get_sample_rows

MAX_RETRIES = 3

SYSTEM_TEMPLATE = """You are an expert SQL assistant for SQLite databases.
Your job is to convert natural language questions into valid SQLite SELECT queries.

Rules:
- Only generate SELECT statements. Never use DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE.
- Use exact table and column names from the schema below.
- Always qualify ambiguous column names with table names (e.g., sales.sale_date).
- Return ONLY the raw SQL query — no markdown, no explanation, no backticks.
- If aggregating, always include a GROUP BY clause.
- Prefer readable aliases for calculated columns.

{schema}

{samples}
"""

CORRECTION_TEMPLATE = """The following SQL query failed with an error. Fix it and return only the corrected SQL.

Original question: {question}
Failed SQL:
{sql}

Error message:
{error}

Return ONLY the corrected SQL query, no explanations.
"""


def _extract_sql(raw: str) -> str:
    """Strip markdown code fences if LLM wraps response."""
    raw = raw.strip()
    # Remove ```sql ... ``` or ``` ... ```
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw


def generate_sql(question: str) -> str:
    """Generate SQL from a natural language question using schema-aware prompting."""
    schema_str = get_schema_prompt()
    sample_str = get_sample_rows()

    system = SYSTEM_TEMPLATE.format(schema=schema_str, samples=sample_str)
    raw = chat(system=system, user=question)
    return _extract_sql(raw)


def fix_sql(question: str, failed_sql: str, error: str) -> str:
    """Ask LLM to fix a broken SQL given the error message."""
    schema_str = get_schema_prompt()
    sample_str = get_sample_rows()

    system = SYSTEM_TEMPLATE.format(schema=schema_str, samples=sample_str)
    user = CORRECTION_TEMPLATE.format(question=question, sql=failed_sql, error=error)
    raw = chat(system=system, user=user)
    return _extract_sql(raw)


def generate_sql_with_retry(question: str, executor) -> tuple[str, any, str | None]:
    """
    Full pipeline: generate → validate → execute → self-correct loop.
    Returns (final_sql, dataframe, error_or_None)
    
    `executor` is a callable: executor(sql) -> (df, error)
    """
    from src.sql_validator import validate_sql, ValidationError

    sql = generate_sql(question)

    for attempt in range(MAX_RETRIES):
        # Safety check first
        try:
            validate_sql(sql)
        except ValidationError as ve:
            return sql, None, f"Blocked by safety validator: {ve}"

        df, error = executor(sql)

        if error is None:
            return sql, df, None

        # Self-correction loop
        if attempt < MAX_RETRIES - 1:
            sql = fix_sql(question, sql, error)
        else:
            return sql, None, error

    return sql, None, "Max retries exceeded"