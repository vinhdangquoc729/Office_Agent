import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, load_skill, build_system_prompt
from graph.state import DocQAState
from tools.output_writers import write_report_docx

_SYSTEM = build_system_prompt(
    load_prompt("reporter"),
    load_skill("report-writing"),
)
_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)


def reporter_node(state: DocQAState) -> dict:
    analysis = state.get("analysis", {})
    user_request = state["messages"][-1].content if state.get("messages") else ""

    analysis_text = json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else ""

    response = _llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Yêu cầu: {user_request}\n\n"
            f"Kết quả phân tích:\n{analysis_text}"
        )},
    ])

    report_content = response.content
    report_path = write_report_docx(report_content)

    return {"summary": report_content, "report_path": report_path}
