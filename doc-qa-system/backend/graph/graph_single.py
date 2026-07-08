from langgraph.graph import StateGraph, END

from graph.state import DocQAState
from graph.router import route_after_supervisor
from agents.supervisor import supervisor_node
from agents.document_loader import document_loader_node
from agents.universal_agent import universal_agent_node
from agents.chat import chat_node


def _route_after_supervisor_single(state: DocQAState) -> str:
    """Same logic as route_after_supervisor but routes analyst → universal_agent."""
    if state.get("request_type") == "chat":
        return "chat"
    if not state.get("file_content") or state.get("need_document", True):
        return "document_loader"
    return "universal_agent"


def build_graph_single(checkpointer):
    g = StateGraph(DocQAState)

    g.add_node("supervisor", supervisor_node)
    g.add_node("chat", chat_node)
    g.add_node("document_loader", document_loader_node)
    g.add_node("universal_agent", universal_agent_node)

    g.set_entry_point("supervisor")
    g.add_conditional_edges(
        "supervisor",
        _route_after_supervisor_single,
        {"chat": "chat", "document_loader": "document_loader", "universal_agent": "universal_agent"},
    )
    g.add_edge("chat", END)
    g.add_edge("document_loader", "universal_agent")
    g.add_edge("universal_agent", END)

    return g.compile(checkpointer=checkpointer)
