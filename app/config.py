import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # GCP Core
    PROJECT_ID = os.getenv("PROJECT_ID", "enterprise-rag-509108")
    LOCATION = os.getenv("LOCATION", "us-central1")
    GCP_DOC_AI_LOCATION = os.getenv("GCP_DOC_AI_LOCATION", "us")
    GCP_DOC_AI_PROCESSOR_ID = os.getenv("GCP_DOC_AI_PROCESSOR_ID")
    RAW_BUCKET = os.getenv("GCP_RAW_BUCKET", "enterprise0-rag-raw")
    PROCESSED_BUCKET = os.getenv("GCP_PROCESSED_BUCKET", "enterprise0-rag-processed")

    # Vector DB (Qdrant)
    QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = "enterprise_rag"

    # LLM (Groq)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")
    GROQ_MODEL = "qwen/qwen3.8-27b"
    GUARD_MODEL = "openai/gpt-oss-20b"

      # --- LLM Gateway (Portkey) ---
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
    PORTKEY_CONFIG_ID = os.getenv("PORTKEY_CONFIG_ID")
    GROQ_SLUG = "rag"     # primary virtual key: @rag/llama-3.3-70b-versatile
    GROQ_SLUG_2 = "brag"  # fallback virtual key: @brag/llama-3.1-8b-instant


    # Observability
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "enterprise-rag")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")


    # Apply LangSmith env vars for automatic LangChain tracing (only if set)
    @staticmethod
    def _apply_langsmith_env():
        _mapping = {
            "LANGCHAIN_TRACING_V2": "LANGSMITH_TRACING",
            "LANGCHAIN_API_KEY": "LANGSMITH_API_KEY",
            "LANGCHAIN_PROJECT": "LANGSMITH_PROJECT",
            "LANGCHAIN_ENDPOINT": "LANGSMITH_ENDPOINT",
        }
        for target, source in _mapping.items():
            value = os.getenv(source)
            if value:
                os.environ[target] = value

settings = Settings()
settings._apply_langsmith_env()