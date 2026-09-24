import re
import logfire

from app.agents.state import AgentState
from app.gateway import get_langchain_llm


llm = get_langchain_llm(feature="planner")

# Canned response for off-topic queries -- returned directly, no extra LLM call.
_BLOCKED_RESPONSE = (
    "I'm an Enterprise IT Assistant focused on Kubernetes, infrastructure, "
    "and networking. I can't help with that -- but ask me anything technical!"
)


def planner_node(state: AgentState):

    messages = state.get("messages", [])

    history = ""

    for msg in messages[:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history += f"{role}: {msg['content']}\n"

    user_message = (
        messages[-1]["content"]
        if messages
        else ""
    )

    prompt = f"""
You are the routing planner and content gate for an Enterprise RAG system.
Classify the CURRENT USER MESSAGE into exactly one category.

CONVERSATION HISTORY:
{history}

CURRENT USER MESSAGE:
{user_message}

CATEGORIES:

BLOCKED
The message is off-topic or unrelated to enterprise IT.
Return exactly: BLOCKED
Off-topic examples: jokes, recipes, general knowledge, sports, movies,
weather, math homework, poetry, travel advice, relationship advice,
what is the capital of France, write me a poem, recommend a movie.

CONVERSATIONAL
Casual greeting, farewell, or answerable from conversation history.
Return exactly: CONVERSATIONAL
Examples: hi, hello, bye, what did I ask, summarize our chat,
what is my name, what did we discuss earlier.

TECHNICAL
Any question about Kubernetes, Docker, networking, databases, DevOps,
cloud, programming, infrastructure, or enterprise technology.
Return a concise search query (NOT the word TECHNICAL).
Examples:
  "how do I autoscale pods on kubernetes" -> autoscale kubernetes pods
  "what is Kubernetes HPA" -> kubernetes HPA
  "explain Docker networking" -> docker networking

RULES:
- Judge the CURRENT USER MESSAGE only.
- Technical questions are NEVER off-topic.
- When in doubt, classify as TECHNICAL.
- Do NOT answer the question.
- Do NOT explain your decision.
- Return ONLY one of: BLOCKED, CONVERSATIONAL, or a search query.

CURRENT USER MESSAGE:
{user_message}
"""

    with logfire.span("[Planner] Decision"):
        raw = llm.invoke(prompt).content.strip()
        # Strip <think> tags if model includes reasoning (Qwen models)
        decision = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        decision = decision.strip("\"'`").split("\n")[0].strip()
        logfire.info(f"Intent identified: {decision}")

    if decision == "BLOCKED":
        logfire.info("[Planner] Off-topic query blocked.")
        return {
            "current_query": "BLOCKED",
            "final_answer": _BLOCKED_RESPONSE,
            "status": "Blocked by content policy.",
            "plan": ["Intent: Off-topic", "Action: Blocked"],
            "messages": [{"role": "assistant", "content": _BLOCKED_RESPONSE}]
        }

    if decision == "CONVERSATIONAL":
        return {
            "current_query": "CONVERSATIONAL",
            "status": "Handling conversationally (using memory)...",
            "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
        }

    return {
        "current_query": decision,
        "status": f"Technical research needed. Searching for: {decision}",
        "plan": ["Intent: Technical", f"Search Term: {decision}"]
    }