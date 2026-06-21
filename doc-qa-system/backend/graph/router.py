from graph.state import DocQAState


def route_after_supervisor(state: DocQAState) -> str:
    if state.get("request_type") == "chat":
        return "chat"
    # Safety: nếu chưa có content thì bắt buộc load dù supervisor nói gì
    if not state.get("file_content") or state.get("need_document", True):
        return "document_loader"
    return "analyst"


def route_after_analyst(state: DocQAState) -> str:
    request_type = state.get("request_type", "analyze")
    if request_type in ("report", "slide"):
        return "reporter"
    elif request_type in ("analyze", "qa"):
        return "response_maker"
    else:
        # summarize → summarizer
        return "summarizer"


def route_after_reporter(state: DocQAState) -> str:
    if state.get("request_type") == "slide":
        return "slide_creator"
    return "__end__"
