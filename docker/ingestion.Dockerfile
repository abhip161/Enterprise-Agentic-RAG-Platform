FROM python:3.11-slim-bookworm

WORKDIR /app

# Install deps first for layer caching
COPY requirements-ingestion.txt .
RUN pip install --no-cache-dir -r requirements-ingestion.txt

# Copy ingestion + shared services code
COPY app/__init__.py ./app/
COPY app/config.py ./app/
COPY app/ingestion/ ./app/ingestion/
COPY app/services/ ./app/services/

EXPOSE 8080

CMD ["uvicorn", "app.ingestion.processor:app", "--host", "0.0.0.0", "--port", "8080"]
