"""
app.py — Streamlit UI for Talk-to-Data.

Run: streamlit run app.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.io as pio
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Talk-to-Data 🗂️",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🗂️ Talk-to-Data")
    st.markdown("Ask natural language questions about the **Sales Database**.")
    st.divider()

    st.subheader("📊 Sample Questions")
    examples = [
        "What are the top 5 products by total revenue?",
        "Show monthly sales trend for 2023",
        "Which product category has the highest average order value?",
        "Who are the top 10 customers by total spending?",
        "What is the total revenue by region?",
        "How many orders were placed each month?",
        "What is the best-selling product in the Electronics category?",
        "Compare revenue across different regions",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["question_input"] = ex

    st.divider()

    # Schema viewer
    with st.expander("🗄️ View Database Schema"):
        try:
            resp = requests.get(f"{API_URL}/schema", timeout=5)
            if resp.ok:
                st.code(resp.json()["schema"], language="sql")
            else:
                st.warning("Could not load schema.")
        except Exception:
            st.warning("API not reachable. Start the backend first.")

# ─── Main Area ────────────────────────────────────────────────────────────────
st.title("🗂️ Talk-to-Data")
st.caption("Powered by LLM + FastAPI + SQLite | Ask anything about your data")

question = st.text_input(
    "Ask a question about your data:",
    placeholder="e.g. What are the top 5 products by revenue?",
    key="question_input",
)

run_btn = st.button("🔍 Run Query", type="primary", use_container_width=False)

if run_btn and question.strip():
    with st.spinner("🤔 Thinking..."):
        try:
            resp = requests.post(
                f"{API_URL}/query",
                json={"question": question},
                timeout=60,
            )
            result = resp.json()
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the FastAPI backend is running on port 8000.")
            st.code("uvicorn backend.main:app --reload --port 8000")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    # ── Error handling ────────────────────────────────────────────────────────
    if result.get("error"):
        st.error(f"❌ Query failed: {result['error']}")
        if result.get("sql"):
            st.subheader("🔎 Generated SQL")
            st.code(result["sql"], language="sql")
        st.stop()

    # ── Layout: 4 sections ────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("🔎 Generated SQL")
        st.code(result["sql"], language="sql")

        st.subheader("💬 Explanation")
        st.info(result["explanation"])

    with col2:
        st.subheader(f"📋 Results ({result['row_count']} rows)")
        if result["data"]:
            df = pd.DataFrame(result["data"])
            st.dataframe(df, use_container_width=True, height=280)
        else:
            st.warning("No data returned.")

    # ── Chart ─────────────────────────────────────────────────────────────────
    if result.get("chart"):
        st.subheader("📈 Auto-Generated Visualization")
        fig = pio.from_json(result["chart"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No chart generated for this result shape.")

elif run_btn:
    st.warning("Please enter a question first.")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("Built with Streamlit · FastAPI · OpenAI · SQLite · Plotly")