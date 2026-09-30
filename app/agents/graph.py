import os
import logfire
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retriever import retrieve_node
from app.agents.nodes.responder import generate_node


# 1. Initialize the State Graph
workflow = StateGraph(AgentState)


# 2. Define the Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retrieve_node)
workflow.add_node("responder", generate_node)

# 3. Define the Edges & Routing Logic
def route_planner(state: AgentState):
    """
    Routes the workflow based on the planner's decision.
    """
    if state["current_query"] == "CONVERSATIONAL":
        return "responder"
    return "retriever"

workflow.set_entry_point("planner")


# Conditional Edge: Planner -> Router -> (Retriever OR Responder)
workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "retriever": "retriever",
        "responder": "responder"
    }
)


workflow.add_edge("retriever", "responder")
workflow.add_edge("responder", END)


# --- MEMORY UPGRADE ---
# Hybrid checkpointer: PostgresSaver (Cloud SQL) in production, MemorySaver (RAM) locally.
LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() == "true"


def _build_checkpointer():
    """
    Build the appropriate checkpointer based on environment.

    - LOCAL_MODE=true  → MemorySaver (RAM) — no database needed for local dev
    - LOCAL_MODE=false → PostgresSaver (Cloud SQL) — persistent conversation memory
    - Fallback         → MemorySaver if DB is unreachable
    """
    if LOCAL_MODE:
        logfire.info("🧠 Using MemorySaver (LOCAL_MODE=true)")
        return MemorySaver()

    try:
        from app.services.gcp.database_service import get_db_pool
        from langgraph.checkpoint.postgres import PostgresSaver

        pool = get_db_pool()
        if pool is None:
            logfire.warning("🧠 DB pool unavailable — falling back to MemorySaver")
            return MemorySaver()

        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        logfire.info("🧠 Using PostgresSaver (Cloud SQL) — persistent memory enabled")
        return checkpointer

    except Exception as e:
        logfire.error("🧠 PostgresSaver init failed: {error} — falling back to MemorySaver", error=str(e))
        return MemorySaver()


checkpointer = _build_checkpointer()


# 4. Compile the Graph with Memory
rag_agent = workflow.compile(checkpointer=checkpointer)