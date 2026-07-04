from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt
from agents.i18n import lbl
from graph.state import DocQAState

_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(load_prompt("chat", lang))
    for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o", temperature=0.3)


def chat_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    history = state.get("messages", [])
    system = _SYSTEMS.get(lang, _SYSTEMS["vi"])

    messages = [{"role": "system", "content": system + lbl(lang, "lang_note")}]
    for msg in history:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})

    response = _llm.invoke(messages)
    return {"summary": response.content}
