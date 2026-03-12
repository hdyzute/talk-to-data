"""
explainer.py — Generate natural language explanations of query results using LLM.
"""

import pandas as pd
from src.llm import chat

SYSTEM_PROMPT = """You are a data analyst assistant. 
Given a user's question, the SQL query used, and a summary of the query results, 
provide a clear and concise natural language explanation (2-4 sentences).
Focus on key insights, trends, or notable values in the data.
Be specific with numbers. Do not repeat the SQL."""


def summarize_dataframe(df: pd.DataFrame, max_rows: int = 10) -> str:
    """Create a compact text summary of a DataFrame for the LLM."""
    if df is None or df.empty:
        return "No results returned."

    lines = [
        f"Rows: {len(df)}, Columns: {list(df.columns)}",
        f"Data types: {df.dtypes.to_dict()}",
    ]

    # Stats for numeric cols
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        stats = df[num_cols].describe().round(2).to_dict()
        lines.append(f"Numeric summary: {stats}")

    # Sample rows
    sample = df.head(max_rows).to_dict(orient="records")
    lines.append(f"Sample rows: {sample}")

    return "\n".join(lines)


def explain_result(question: str, sql: str, df: pd.DataFrame) -> str:
    """
    Generate a natural language explanation of query results.
    Returns explanation string.
    """
    if df is None or df.empty:
        return "The query returned no results."

    summary = summarize_dataframe(df)
    user_prompt = f"""User question: {question}

SQL used:
{sql}

Query result summary:
{summary}

Please explain what this data shows in plain English."""

    return chat(system=SYSTEM_PROMPT, user=user_prompt, temperature=0.3, max_tokens=256)