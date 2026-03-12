# 🗂️ Talk-to-Data — AI-Powered Natural Language Data Assistant

> Ask questions in plain English. Get SQL, data tables, charts, and explanations automatically.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────┐
│                   USER                          │
│         "Top 5 products by revenue?"            │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              STREAMLIT UI  (app.py)             │
│  • Text input  • SQL display  • Results table   │
│  • Plotly chart  • Explanation text             │
└─────────────────────┬───────────────────────────┘
                      │  POST /query
                      ▼
┌─────────────────────────────────────────────────┐
│           FASTAPI BACKEND  (backend/main.py)    │
└──────┬───────────────────────────────┬──────────┘
       │                               │
       ▼                               ▼
┌──────────────────┐        ┌──────────────────────┐
│  SQL GENERATOR   │        │   SCHEMA LOADER      │
│  (llm.py +       │◄───────│   (schema_loader.py) │
│  sql_generator)  │ schema │   Extract tables,    │
│                  │ inject │   columns, samples   │
│  OpenAI GPT-4o   │        └──────────────────────┘
└──────┬───────────┘
       │ generated SQL
       ▼
┌─────────────────────────────────────────────────┐
│            SQL VALIDATOR  (sql_validator.py)    │
│  Block: DROP / DELETE / UPDATE / INSERT / ALTER │
│  Allow: SELECT only                             │
└──────┬──────────────────────────────────────────┘
       │ safe SQL
       ▼
┌─────────────────────────────────────────────────┐
│           DATABASE  (database.py)               │
│           SQLite  data/sales.db                 │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │  Self-Correction Loop (up to 3 retries) │  │
│   │  Error → LLM → Fixed SQL → Retry        │  │
│   └─────────────────────────────────────────┘  │
└──────┬──────────────────────────────────────────┘
       │ pandas DataFrame
       ▼
┌─────────────────────────────────────────────────┐
│         VISUALIZATION  (visualization.py)       │
│  time col → Line chart                          │
│  category + value → Bar chart                   │
│  2 numerics → Scatter plot                      │
│  1 numeric → Histogram                          │
└──────┬──────────────────────────────────────────┘
       │ Plotly JSON
       ▼
┌─────────────────────────────────────────────────┐
│         LLM EXPLAINER  (explainer.py)           │
│  DataFrame summary → GPT → Plain English result │
└─────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
talk-to-data/
├── data/
│   ├── sales.db          # SQLite database (auto-created)
│   └── seed_db.py        # Database seeding script
├── src/
│   ├── database.py       # DB connection & query execution
│   ├── schema_loader.py  # Schema extraction for LLM context
│   ├── llm.py            # OpenAI client wrapper
│   ├── sql_generator.py  # LLM-based SQL generation + self-correction
│   ├── sql_validator.py  # SQL safety guardrails
│   ├── visualization.py  # Auto chart generation (Plotly)
│   └── explainer.py      # LLM result explanation
├── backend/
│   └── main.py           # FastAPI service (POST /query)
├── evaluation/
│   ├── dataset.json      # 10 question → expected SQL pairs
│   └── eval.py           # Evaluation: exec accuracy + exact match
├── app.py                # Streamlit UI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourname/talk-to-data
cd talk-to-data

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Seed the Database

```bash
python data/seed_db.py
```

### 4. Start the Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 5. Start the UI

```bash
streamlit run app.py
```

Open: `http://localhost:8501`

---

## 🐳 Docker

```bash
# Build
docker build -t talk-to-data .

# Run backend only
docker run -p 8000:8000 --env-file .env talk-to-data

# Or use docker-compose (backend + frontend together)
docker-compose up --build
```

---

## 🔌 API Reference

### `POST /query`

**Request:**
```json
{
  "question": "What are the top 5 products by total revenue?"
}
```

**Response:**
```json
{
  "question": "What are the top 5 products by total revenue?",
  "sql": "SELECT p.product_name, SUM(s.total_amount) AS total_revenue FROM sales s JOIN products p ON s.product_id = p.product_id GROUP BY p.product_name ORDER BY total_revenue DESC LIMIT 5",
  "data": [...],
  "columns": ["product_name", "total_revenue"],
  "row_count": 5,
  "chart": "{...plotly json...}",
  "explanation": "The top product is Laptop with $48,234 in revenue...",
  "error": null
}
```

### `GET /schema`
Returns the full database schema as a formatted string.

### `GET /health`
Health check endpoint.

---

## 💬 Example Questions

| Question | Chart Type |
|----------|------------|
| What are the top 5 products by revenue? | Bar chart |
| Show monthly sales trend for 2023 | Line chart |
| Which product category earns the most? | Bar chart |
| Who are the top 10 customers by spending? | Bar chart |
| What is the revenue distribution? | Histogram |
| Compare sales across regions | Bar chart |

---

## 🧪 Evaluation

Run the evaluation script to measure SQL generation quality:

```bash
python -m evaluation.eval
```

**Metrics:**
- **Exact Match** — Generated SQL matches expected SQL (normalized)
- **Execution Accuracy** — Both SQLs return the same data result

Sample output:
```
============================================================
  Talk-to-Data Evaluation — 10 questions
============================================================

✅ [1] What is the total revenue from all sales?
✅ [2] What are the top 5 products by total revenue?
✅ [3] How many sales were made each month in 2023?
...

============================================================
  RESULTS SUMMARY
============================================================
  Total questions   : 10
  Exact SQL match   : 6/10 (60.0%)
  Execution accuracy: 9/10 (90.0%)
============================================================
```

---

## 🛡️ Safety Guardrails

The SQL Validator (`src/sql_validator.py`) blocks all non-SELECT operations:

| Blocked Keywords | Reason |
|-----------------|--------|
| DROP | Would delete tables |
| DELETE | Would remove rows |
| UPDATE | Would modify data |
| INSERT | Would add data |
| ALTER | Would change schema |
| TRUNCATE | Would empty tables |

The SQLite database is also opened in **read-only mode** as a defense-in-depth measure.

---

## 🔁 Self-Correction Loop

If the generated SQL fails to execute:

1. The error message is captured
2. Original question + failed SQL + error → sent back to LLM
3. LLM generates corrected SQL
4. Retry up to **3 times** before returning an error

---

## 🤖 AI Pipeline Details

| Component | Technology |
|-----------|-----------|
| LLM | OpenAI GPT-4o-mini (configurable) |
| Prompting | Schema-aware system prompt injection |
| SQL Generation | Zero-shot + self-correction |
| Safety | Keyword blocklist + read-only SQLite |
| Visualization | Rule-based chart selection (Plotly) |
| Explanation | LLM with DataFrame summary context |

---

## 📄 License

MIT — Free to use in your portfolio, projects, and applications.