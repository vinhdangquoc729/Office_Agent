import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt, parse_json_response
from graph.state import DocQAState

_SYSTEM = build_system_prompt(load_prompt("supervisor"))
_llm = ChatOpenAI(model="gpt-4o", temperature=0)


def supervisor_node(state: DocQAState) -> dict:
    last_msg = state["messages"][-1].content if state.get("messages") else ""
    has_document = bool(state.get("file_content"))

    response = _llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"has_document: {str(has_document).lower()}\n"
            f"Yêu cầu người dùng: {last_msg}"
        )},
    ])
    try:
        result = parse_json_response(response.content)
        return {
            "request_type": result.get("request_type", "analyze"),
            "need_document": result.get("need_document", not has_document),
        }
    except Exception:
        return {
            "request_type": "analyze",
            "need_document": not has_document,
        }
