"""
backend/main.py — FastAPI service exposing the Talk-to-Data pipeline.

Endpoints:
  POST /query   — Main pipeline: question → SQL → data → chart → explanation
  GET  /schema  — Expose database schema
  GET  /health  — Health check
"""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from src.database import execute_query
from src.sql_generator import generate_sql_with_retry
from src.sql_validator import validate_sql, ValidationError
from src.visualization import auto_visualize, fig_to_json
from src.explainer import explain_result
from src.schema_loader import get_schema_prompt


app = FastAPI(
    title="Talk-to-Data API",
    description="Convert natural language questions to SQL and return structured results.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str

    class Config:
        json_schema_extra = {
            "example": {"question": "What are the top 5 products by total sales?"}
        }


class QueryResponse(BaseModel):
    question: str
    sql: str
    data: list[dict]          # List of row dicts
    columns: list[str]
    row_count: int
    chart: str                # Plotly JSON string (empty if no chart)
    explanation: str
    error: str | None = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "talk-to-data"}


@app.get("/schema")
def schema():
    """Return the full database schema as a formatted string."""
    return {"schema": get_schema_prompt()}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Main pipeline:
    1. Generate SQL from natural language (schema-aware)
    2. Validate SQL for safety
    3. Execute SQL (with self-correction on failure)
    4. Build DataFrame
    5. Auto-generate chart
    6. Generate explanation
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # ── Step 1–3: Generate + validate + execute with retry ────────────────────
    sql, df, error = generate_sql_with_retry(question, executor=execute_query)

    if error:
        return QueryResponse(
            question=question,
            sql=sql or "",
            data=[],
            columns=[],
            row_count=0,
            chart="",
            explanation="",
            error=error,
        )

    # ── Step 4: Chart ─────────────────────────────────────────────────────────
    fig = auto_visualize(df, title=question[:80])
    chart_json = fig_to_json(fig)

    # ── Step 5: Explanation ───────────────────────────────────────────────────
    explanation = explain_result(question, sql, df)

    return QueryResponse(
        question=question,
        sql=sql,
        data=df.to_dict(orient="records"),
        columns=list(df.columns),
        row_count=len(df),
        chart=chart_json,
        explanation=explanation,
        error=None,
    )

