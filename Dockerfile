FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data directory and seed database
RUN python data/seed_db.py

# Expose ports: 8000 (FastAPI) + 8501 (Streamlit)
EXPOSE 8000 8501

# Default: start FastAPI backend
# For Streamlit: override CMD with: streamlit run app.py
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]