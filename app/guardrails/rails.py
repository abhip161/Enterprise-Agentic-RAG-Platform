"""
Lightweight keyword-based guardrails for jailbreak / prompt-injection detection.

Off-topic content filtering is handled by the planner node using a single
LLM classification call, replacing the NeMo multi-call approach.
"""
import re
import logfire


# Regex patterns for common jailbreak / prompt-injection attempts.
# Checked before any LLM call — zero cost, zero latency.
_JAILBREAK_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+dan",
    r"pretend\s+you\s+have\s+no\s+restrictions",
    r"forget\s+your\s+(system\s+)?prompt",
    r"act\s+as\s+if\s+you\s+were\s+trained\s+differently",
    r"your\s+new\s+instructions\s+are",
    r"disregard\s+your\s+training",
    r"developer\s+mode",
    r"override\s+your\s+safety",
    r"bypass\s+your\s+guidelines",
    r"act\s+as\s+an?\s+unrestricted",
]

_JAILBREAK_RESPONSE = (
    "I maintain consistent guidelines regardless of how I am prompted. "
    "I am here to help with Kubernetes, Intel, and networking. "
    "What can I help you with?"
)


def initialize_rails() -> None:
    """Keyword guardrails require no model loading."""
    logfire.info("[Guardrails] Keyword guard ready.")


def guard(message: str) -> tuple[bool, str | None]:
    """
    Fast keyword guard for jailbreak / prompt-injection detection.

    Off-topic filtering is handled by the planner node's expanded
    classification (BLOCKED / CONVERSATIONAL / search query), so this
    function only checks for jailbreak patterns.

    Returns:
        (True,  response) -- jailbreak detected; return this response.
        (False, None)     -- message is clean; proceed to the graph.
    """
    lower = message.lower().strip()
    for pattern in _JAILBREAK_PATTERNS:
        if re.search(pattern, lower):
            logfire.info(f"[Guardrails] Jailbreak blocked | query='{message[:80]}'")
            return True, _JAILBREAK_RESPONSE

    logfire.info("[Guardrails] Passed.")
    return False, None
