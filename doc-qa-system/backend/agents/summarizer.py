from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt
from agents.i18n import lbl
from graph.state import DocQAState

_SYSTEM = build_system_prompt(load_prompt("summarizer"))
_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)


def summarizer_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    content = state.get("file_content", "")
    analysis = state.get("analysis", {})
    user_request = state["messages"][-1].content if state.get("messages") else ""

    # Nếu analyst trả về data thô (danh sách, bảng), pass through không nén thêm
    raw_data = analysis.get("data", "")
    if raw_data:
        prose = analysis.get("prose_summary", "")
        summary = f"{prose}\n\n{raw_data}".strip() if prose else raw_data
        return {"summary": summary}

    input_text = analysis.get("prose_summary", "") or content[:8000]

    response = _llm.invoke([
        {"role": "system", "content": _SYSTEM + lbl(lang, "lang_note")},
        {"role": "user", "content": (
            f"{lbl(lang, 'request')}: {user_request}\n\n"
            f"{lbl(lang, 'summary_content')}:\n{input_text}"
        )},
    ])

    return {"summary": response.content}
