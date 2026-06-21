from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt
from graph.state import DocQAState

_SYSTEM = build_system_prompt(load_prompt("chat"))
_llm = ChatOpenAI(model="gpt-4o", temperature=0.3)


def chat_node(state: DocQAState) -> dict:
    history = state.get("messages", [])

    messages = [{"role": "system", "content": _SYSTEM}]
    for msg in history:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})

    response = _llm.invoke(messages)
    return {"summary": response.content}
