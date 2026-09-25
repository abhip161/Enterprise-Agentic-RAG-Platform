"""
LLM Gateway — Portkey proxy layer.

Provides two clients for different use cases:
  • portkey_client  (native SDK)  → responder node; exposes response headers
                                    so we can read x-portkey-cache-status.
  • get_langchain_llm()           → planner node;  returns ChatOpenAI that
                                    speaks the standard .invoke() interface
                                    LangGraph expects.

All LLM traffic flows through Portkey, giving us retry, fallback,
caching, and full observability for free.
"""

import os

from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI

from app.config import settings


# Gateway configuration
# The full routing strategy (fallback, retry, cache, targets) is saved in the
# Portkey dashboard as a Config and referenced by its pc-... slug.  Inline
#
# Dashboard config contains:
#   strategy:        fallback
#   cache:           semantic (Enterprise) / simple (free)
#   retry:           2 attempts on [429, 503]
#   request_timeout: 30 000 ms
#   targets:         @rag/qwen/qwen3.8-27b  →  @brag/qwen/qwen3.8-27b

GATEWAY_CONFIG_ID = settings.PORTKEY_CONFIG_ID


# Native Portkey client (used by responder for header-level cache detection)

portkey_client = Portkey(
    api_key=settings.PORTKEY_API_KEY,
    config=GATEWAY_CONFIG_ID,
)


# LangChain-compatible LLM factory (used by planner, keeps .invoke() API)

def get_langchain_llm(
    *,
    temperature: float = 0,
    metadata: dict | None = None,
) -> ChatOpenAI:
    """
    Return a ChatOpenAI instance that routes through the Portkey gateway.

    Why ChatOpenAI and not ChatGroq?
    ChatGroq hard-codes the Groq base_url — we need to point at Portkey
    instead.  ChatOpenAI accepts any base_url and speaks the same
    OpenAI-compatible format that Portkey (and Groq) expose.
    """
    headers = createHeaders(
        api_key=settings.PORTKEY_API_KEY,
        config=GATEWAY_CONFIG_ID,
        metadata=metadata or {"feature": "rag-pipeline", "_user": "system"},
    )

    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        # Model is governed by GATEWAY_CONFIG targets; this is a display hint
        model="@rag/qwen/qwen3.8-27b",
        temperature=temperature,
        default_headers=headers,
    )

# Cache-status helper

def extract_cache_status(response) -> str:
    """
    Try to read the ``x-portkey-cache-status`` header from a native
    Portkey SDK response.

    The SDK does not expose headers on the plain ``.create()`` return
    object.  We walk several private-attribute paths that different
    SDK versions may use.  If none are found we return ``"MISS"`` —
    the cache still works server-side and the dashboard will show hits;
    this label is best-effort for the UI.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            headers = getattr(raw, "headers", {})
            status = (
                headers.get("x-portkey-cache-status", "")
                if isinstance(headers, dict)
                else getattr(headers, "get", lambda *a: "")(
                    "x-portkey-cache-status", ""
                )
            )
            if status:
                return status.upper()
    return "MISS"
