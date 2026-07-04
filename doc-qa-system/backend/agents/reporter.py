import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, load_skill, build_system_prompt
from agents.i18n import lbl
from graph.state import DocQAState
from tools.output_writers import write_report_docx

_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(load_prompt("reporter", lang), load_skill("report-writing", lang))
    for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)


def reporter_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    analysis = state.get("analysis", {})
    user_request = state["messages"][-1].content if state.get("messages") else ""

    analysis_text = json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else ""

    system = _SYSTEMS.get(lang, _SYSTEMS["vi"])
    response = _llm.invoke([
        {"role": "system", "content": system + lbl(lang, "lang_note")},
        {"role": "user", "content": (
            f"{lbl(lang, 'request')}: {user_request}\n\n"
            f"{lbl(lang, 'analysis_result')}:\n{analysis_text}"
        )},
    ])

    report_content = response.content
    report_path = write_report_docx(report_content)

    return {"summary": report_content, "report_path": report_path}
