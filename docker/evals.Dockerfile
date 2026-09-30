FROM python:3.11-slim-bookworm

WORKDIR /app

# Install deps first for layer caching
COPY requirements-evals.txt .
RUN pip install --no-cache-dir -r requirements-evals.txt

# Copy evals code
COPY evals/ ./evals/

EXPOSE 8080

CMD ["streamlit", "run", "evals/app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
