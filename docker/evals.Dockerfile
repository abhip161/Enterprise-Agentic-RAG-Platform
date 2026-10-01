FROM python:3.11-slim-bookworm

WORKDIR /app

# Install deps first for layer caching
COPY requirements-evals.txt .
RUN pip install --no-cache-dir -r requirements-evals.txt

# Compatibility fix for Ragas 0.4.3 + LangChain 1.x
RUN python -c "from pathlib import Path; p=Path('/usr/local/lib/python3.11/site-packages/ragas/llms/base.py'); s=p.read_text(); s=s.replace('from langchain_community.chat_models.vertexai import ChatVertexAI\nfrom langchain_community.llms import VertexAI', 'from langchain_google_vertexai import ChatVertexAI, VertexAI'); p.write_text(s)"

# Copy evals code
COPY evals/ ./evals/

EXPOSE 8080

CMD ["streamlit", "run", "evals/app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
