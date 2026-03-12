"""
sql_validator.py — basic SQL safety checks used by the self‑correction pipeline.

This module isnt complicated; it simply inspects the string returned by the
LLM and raises a ValidationError if the query looks unsafe.  At present the
only requirement is that the SQL be a single SELECT statement with no harmful
keywords or extra statements.  The generator functions in
`sql_generator.py` import this module, which is why the missing file produced
an import error.
"""

import re


class ValidationError(Exception):
    """Raised when a candidate SQL statement fails a safety check."""


# list of tokens that are never allowed in generated SQL
_FORBIDDEN_KEYWORDS = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "exec",
    "attach",
    "detach",
    "pragma",  # some PRAGMAs can modify data
]


def validate_sql(sql: str) -> None:
    """Validate a SQL string and raise :class:`ValidationError` if it fails.

    The currently enforced rules are intentionally simple:

    * The statement must start with the keyword ``SELECT`` (case‑insensitive).
    * Only one statement is allowed (no semicolons except maybe at the
      very end).
    * None of the forbidden keywords may appear anywhere in the text.

    These checks are meant as a lightweight, fast safety net for the LLM loop;
    they are *not* a substitute for real database permissions.
    """
    text = sql.strip()
    if not text:
        raise ValidationError("empty SQL")

    # drop trailing semicolon for analysis
    if text.endswith(";"):
        text = text[:-1].strip()

    lower = text.lower()

    # only SELECT statements are permitted
    if not lower.startswith("select"):
        raise ValidationError("only SELECT statements are permitted")

    # disallow multiple statements
    if ";" in lower:
        raise ValidationError("multiple SQL statements are not allowed")

    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            raise ValidationError(f"forbidden keyword detected: {kw}")


# quick sanity check when invoking as script
if __name__ == "__main__":
    for q in [
        "SELECT * FROM sales",
        "INSERT INTO sales VALUES (1,2,3)",
        "SELECT * FROM sales; DROP TABLE sales;",
    ]:
        try:
            validate_sql(q)
            print(f"Passed: {q}")
        except ValidationError as e:
            print(f"Blocked: {q} -> {e}")
