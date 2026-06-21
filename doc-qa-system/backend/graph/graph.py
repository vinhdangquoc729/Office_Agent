from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import DocQAState
from graph.router import route_after_supervisor, route_after_analyst, route_after_reporter
from agents.supervisor import supervisor_node
from agents.document_loader import document_loader_node
from agents.analyst import analyst_node
from agents.summarizer import summarizer_node
from agents.reporter import reporter_node
from agents.slide_creator import slide_creator_node
from agents.chat import chat_node
from agents.response_maker import response_maker_node


def build_graph():
    g = StateGraph(DocQAState)

    g.add_node("supervisor", supervisor_node)
    g.add_node("chat", chat_node)
    g.add_node("response_maker", response_maker_node)
    g.add_node("document_loader", document_loader_node)
    g.add_node("analyst", analyst_node)
    g.add_node("summarizer", summarizer_node)
    g.add_node("reporter", reporter_node)
    g.add_node("slide_creator", slide_creator_node)

    g.set_entry_point("supervisor")
    g.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"chat": "chat", "document_loader": "document_loader", "analyst": "analyst"},
    )
    g.add_edge("chat", END)
    g.add_edge("document_loader", "analyst")

    g.add_conditional_edges(
        "analyst",
        route_after_analyst,
        {"reporter": "reporter", "summarizer": "summarizer", "response_maker": "response_maker"},
    )
    g.add_edge("response_maker", END)

    g.add_conditional_edges(
        "reporter",
        route_after_reporter,
        {"slide_creator": "slide_creator", "__end__": END},
    )

    g.add_edge("summarizer", END)
    g.add_edge("slide_creator", END)

    return g.compile(checkpointer=MemorySaver())


graph_app = build_graph()
