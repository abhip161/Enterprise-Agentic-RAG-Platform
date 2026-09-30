FROM python:3.11-slim-bookworm

WORKDIR /app

# Install deps first for layer caching
COPY requirements-ui.txt .
RUN pip install --no-cache-dir -r requirements-ui.txt

# Copy UI code only
COPY ui/ ./ui/

EXPOSE 8501

CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
