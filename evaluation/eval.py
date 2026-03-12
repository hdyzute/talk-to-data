"""
evaluation/eval.py — Evaluate SQL generation accuracy.

Metrics:
  - Execution Accuracy: Both expected and generated SQL return the same result
  - Exact Match: Generated SQL matches expected SQL (normalized)

Run:
  python -m evaluation.eval
"""

import sys
import json
import re
from pathlib import Path

# Allow src imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.sql_generator import generate_sql
from src.sql_validator import validate_sql, ValidationError
from src.database import execute_query

DATASET_PATH = Path(__file__).parent / "dataset.json"


def normalize_sql(sql: str) -> str:
    """Normalize SQL for exact matching (lowercase, collapse whitespace)."""
    sql = sql.lower().strip()
    sql = re.sub(r"\s+", " ", sql)
    sql = sql.rstrip(";")
    return sql


def dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    """Check if two DataFrames contain the same data (order-insensitive)."""
    if df1.empty and df2.empty:
        return True
    if df1.empty or df2.empty:
        return False
    try:
        df1_sorted = df1.sort_values(by=list(df1.columns)).reset_index(drop=True).round(2)
        df2_sorted = df2.sort_values(by=list(df2.columns)).reset_index(drop=True).round(2)
        df1_sorted.columns = [str(c).lower() for c in df1_sorted.columns]
        df2_sorted.columns = [str(c).lower() for c in df2_sorted.columns]
        return df1_sorted.equals(df2_sorted)
    except Exception:
        return False


def run_evaluation(verbose: bool = True) -> dict:
    dataset = json.loads(DATASET_PATH.read_text())
    results = []

    print(f"\n{'='*60}")
    print(f"  Talk-to-Data Evaluation — {len(dataset)} questions")
    print(f"{'='*60}\n")

    for item in dataset:
        qid = item["id"]
        question = item["question"]
        expected_sql = item["expected_sql"]

        # Generate SQL
        try:
            generated_sql = generate_sql(question)
        except Exception as e:
            generated_sql = ""
            gen_error = str(e)
        else:
            gen_error = None

        # Validate
        try:
            validate_sql(generated_sql)
            valid = True
        except ValidationError:
            valid = False

        # Execute expected
        df_expected, exp_error = execute_query(expected_sql)

        # Execute generated
        df_generated, gen_exec_error = execute_query(generated_sql) if valid else (pd.DataFrame(), "Invalid SQL")

        # Metrics
        exact_match = normalize_sql(generated_sql) == normalize_sql(expected_sql)
        exec_acc = dataframes_equal(df_expected, df_generated)

        result = {
            "id": qid,
            "question": question,
            "expected_sql": expected_sql,
            "generated_sql": generated_sql,
            "exact_match": exact_match,
            "execution_accuracy": exec_acc,
            "valid": valid,
            "error": gen_error or gen_exec_error,
        }
        results.append(result)

        if verbose:
            status = "✅" if exec_acc else "❌"
            print(f"{status} [{qid}] {question}")
            if not exec_acc:
                print(f"   Expected : {expected_sql[:80]}...")
                print(f"   Generated: {generated_sql[:80]}...")
                if gen_error or gen_exec_error:
                    print(f"   Error    : {gen_error or gen_exec_error}")
            print()

    # Summary
    total = len(results)
    exact = sum(r["exact_match"] for r in results)
    exec_acc = sum(r["execution_accuracy"] for r in results)

    summary = {
        "total": total,
        "exact_match": exact,
        "execution_accuracy": exec_acc,
        "exact_match_pct": round(exact / total * 100, 1),
        "execution_accuracy_pct": round(exec_acc / total * 100, 1),
    }

    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total questions   : {total}")
    print(f"  Exact SQL match   : {exact}/{total} ({summary['exact_match_pct']}%)")
    print(f"  Execution accuracy: {exec_acc}/{total} ({summary['execution_accuracy_pct']}%)")
    print(f"{'='*60}\n")

    return summary


if __name__ == "__main__":
    run_evaluation(verbose=True)