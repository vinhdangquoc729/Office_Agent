import json
import re

from langchain_openai import ChatOpenAI

from agents import load_prompt, load_skill, build_system_prompt
from agents.i18n import lbl
from graph.state import DocQAState
from tools.output_writers import create_pptx

_FALLBACK_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(load_prompt("slide_creator", lang), load_skill("slide-creation", lang))
    for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)


def slide_creator_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    analysis = state.get("analysis", {})
    user_request = state["messages"][-1].content if state.get("messages") else ""

    # Analyst đã chuẩn bị outline — slide creator chỉ cần render
    slides = analysis.get("slides") if analysis else None

    # Fallback: analyst có thể nhét slides vào prose_summary dưới dạng code block
    if not slides:
        prose = (analysis or {}).get("prose_summary", "")
        code_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", prose)
        if code_match:
            try:
                inner = json.loads(code_match.group(1))
                slides = inner.get("slides") or None
            except Exception:
                pass

    if slides:
        outline = slides
    else:
        # Fallback: gọi LLM nếu analyst chưa build slides (file không phải PDF, hoặc skill chưa kích hoạt)
        input_text = json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else state.get("summary", "")
        fallback_system = _FALLBACK_SYSTEMS.get(lang, _FALLBACK_SYSTEMS["vi"])
        response = _llm.invoke([
            {"role": "system", "content": fallback_system + lbl(lang, "lang_note")},
            {"role": "user", "content": f"{lbl(lang, 'request')}: {user_request}\n\n{lbl(lang, 'analysis_result')}:\n{input_text}"},
        ])
        raw = response.content.strip()
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
        try:
            outline = json.loads(cleaned)
        except Exception:
            outline = [
                {"layout": "cover", "title": lbl(lang, "slide_fallback_title")},
                {"layout": "bullets", "number": 1, "title": lbl(lang, "slide_fallback_content"), "bullets": [response.content[:200]]},
            ]

    slide_path = create_pptx(outline)
    return {"slide_path": slide_path}
