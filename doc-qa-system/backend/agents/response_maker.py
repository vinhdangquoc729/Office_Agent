import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt
from graph.state import DocQAState

_SYSTEM = build_system_prompt(load_prompt("response_maker"))
_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)


def _format_sources(sources: list) -> str:
    if not sources:
        return ""
    parts = []
    for s in sources:
        page = s.get("page")
        note = s.get("note", "")
        file = s.get("file", "")
        if page:
            label = f"{file} trang {page}" if file else f"Trang {page}"
            parts.append(label + (f" — {note}" if note else ""))
    if not parts:
        return ""
    return "\n\n---\n*Nguồn: " + " · ".join(parts) + "*"


def response_maker_node(state: DocQAState) -> dict:
    analysis = state.get("analysis", {})
    user_request = state["messages"][-1].content if state.get("messages") else ""

    data = analysis.get("data", "")
    sources = analysis.get("sources", [])

    context = json.dumps(
        {k: v for k, v in analysis.items() if k not in ("data", "sources") and v},
        ensure_ascii=False,
        indent=2,
    )

    response = _llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Yêu cầu của người dùng: {user_request}\n\n"
            f"has_data: {bool(data)}\n\n"
            f"Thông tin phân tích:\n{context}"
        )},
    ])

    text = response.content.strip()

    if data and "{{data}}" in text:
        text = text.replace("{{data}}", data)
    elif data:
        text = f"{text}\n\n{data}"

    text += _format_sources(sources)

    return {"summary": text}
