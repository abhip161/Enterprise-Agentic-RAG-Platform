import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI

from app.config import settings


# ---------------------------------------------------------------------------
# Native Portkey client — used in responder.py for direct completions
# so we can read response headers (e.g. x-portkey-cache-status).
#
# Routing is handled by the Portkey UI Config (pc-enterp-*):
#   - Fallback: @rag/qwen/qwen3.8-27b -> @brag/openai/gpt-oss-120b
#   - Cache: simple mode
#   - Retry: 2 attempts on 429 / 503
# ---------------------------------------------------------------------------
portkey_client = Portkey(
    api_key=settings.PORTKEY_API_KEY,
    config=settings.PORTKEY_CONFIG_ID,
)


def get_langchain_llm(feature: str = "rag") -> ChatOpenAI:
    """
    Returns a LangChain ChatOpenAI routed through the Portkey gateway.
    Used by the planner and guardrails nodes.
    """
    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model="qwen/qwen3.8-27b",
        temperature=0,
        default_headers=createHeaders(
            api_key=settings.PORTKEY_API_KEY,
            config=settings.PORTKEY_CONFIG_ID,
            metadata={
                "feature": feature,
                "_user": "rag-system",
                "environment": "production"
            }
        )
    )


def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey native client response headers.
    Tries multiple attribute paths defensively -- returns 'MISS' if not found.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"