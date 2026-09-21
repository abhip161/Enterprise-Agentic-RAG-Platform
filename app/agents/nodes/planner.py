from app.agents.state import AgentState
from app.config import settings
from langchain_groq import ChatGroq
import logfire


llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0,
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
You are the routing planner for an Enterprise RAG system.

Your job is ONLY to decide whether the CURRENT USER MESSAGE
needs conversation memory or enterprise knowledge retrieval.

CONVERSATION HISTORY:
{history}

CURRENT USER MESSAGE:
{user_message}

RULES:

CONVERSATIONAL:
Return exactly CONVERSATIONAL ONLY if the current message
can be answered using the conversation history or is casual
conversation.

Examples:
- hi
- hello
- how are you?
- what is my name?
- what did I ask previously?
- what did we discuss earlier?
- summarize our conversation

TECHNICAL:
Any technical, factual, documentation, how-to,
troubleshooting, programming, infrastructure, cloud,
Kubernetes, Docker, networking, database, DevOps,
architecture, or enterprise knowledge question MUST use
retrieval.

Examples:
- how to autoscale pods on kubernetes
- what is Kubernetes HPA
- how do I configure Redis
- explain Docker networking
- how does this architecture work
- fix this Python error
- how does the deployment work

IMPORTANT:
- Judge the CURRENT USER MESSAGE.
- Do NOT classify a technical question as CONVERSATIONAL.
- Previous conversation must NOT override a technical query.
- Do NOT answer the question.
- Do NOT explain your decision.
- Return ONLY:
  CONVERSATIONAL
  OR
  a concise search query.

CURRENT USER MESSAGE:
{user_message}
"""

    with logfire.span("🧠 Planner Decision"):
        decision = llm.invoke(prompt).content.strip()
        logfire.info(f"Intent identified: {decision}")
    
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