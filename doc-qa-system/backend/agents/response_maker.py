import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt
from agents.i18n import lbl
from graph.state import DocQAState

_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(load_prompt("response_maker", lang))
    for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o", temperature=0.1, streaming=True)


def _format_sources(sources: list, lang: str = "vi") -> str:
    if not sources:
        return ""
    parts = []
    for s in sources:
        page = s.get("page")
        note = s.get("note", "")
        file = s.get("file", "")
        if page:
            label = lbl(lang, "file_page_label", file=file, page=page) if file else lbl(lang, "page_label", page=page)
            parts.append(label + (f" — {note}" if note else ""))
    if not parts:
        return ""
    return f"\n\n---\n*{lbl(lang, 'sources_label')}: " + " · ".join(parts) + "*"


async def response_maker_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    analysis = state.get("analysis", {})
    user_request = state["messages"][-1].content if state.get("messages") else ""

    data = analysis.get("data", "")
    sources = analysis.get("sources", [])

    context = json.dumps(
        {k: v for k, v in analysis.items() if k not in ("data", "sources") and v},
        ensure_ascii=False,
        indent=2,
    )

    system = _SYSTEMS.get(lang, _SYSTEMS["vi"])
    chunks = []
    async for chunk in _llm.astream([
        {"role": "system", "content": system + lbl(lang, "lang_note")},
        {"role": "user", "content": (
            f"{lbl(lang, 'user_request')}: {user_request}\n\n"
            f"has_data: {bool(data)}\n\n"
            f"{lbl(lang, 'analysis_info')}:\n{context}"
        )},
    ]):
        chunks.append(chunk.content)

    text = "".join(chunks).strip()

    if data and "{{data}}" in text:
        text = text.replace("{{data}}", data)
    elif data:
        text = f"{text}\n\n{data}"

    text += _format_sources(sources, lang)

    return {"summary": text}
