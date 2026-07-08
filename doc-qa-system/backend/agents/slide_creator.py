import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from agents import load_prompt, load_skill, build_system_prompt, BASE
from agents.i18n import lbl
from graph.state import DocQAState
from tools.output_writers import run_ts_script, create_pptx
from tools.skill_loader import activate_skill, read_skill_reference, read_skill_script

_REFS_DIR = BASE / "skills" / "slide-creation" / "references"

MAX_ITERATIONS = 8


def _load_ref(name: str, lang: str) -> str:
    for fname in [f"{name}.{lang}.md", f"{name}.md"]:
        p = _REFS_DIR / fname
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(
        load_prompt("slide_creator", lang),
        load_skill("slide-creation", lang),
        load_skill("pptx-slides", lang),
        _load_ref("style-presets", lang),
    )
    for lang in ("vi", "en")
}

_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)


@tool
def read_reference(skill: str, filename: str) -> str:
    """Read a reference file from a skill's references/ directory.
    Use to access detailed API guides, patterns, or templates.
    skill: skill slug (e.g. 'pptx-slides', 'slide-creation')
    filename: file name (e.g. 'pptxgenjs-helpers.md', 'slide-patterns.md')"""
    return read_skill_reference(skill, filename)


@tool
def read_script_file(skill: str, filename: str) -> str:
    """Read a TypeScript source file from a skill's scripts/ directory.
    Use to inspect exact function signatures, exports, and implementation details
    before writing code that imports from those modules.
    skill: skill slug (e.g. 'pptx-slides')
    filename: file name (e.g. 'theme.ts', 'decorative.ts', 'types.ts')"""
    return read_skill_script(skill, filename)


def _validate_ts_images(ts_code: str) -> list[str]:
    """Check addImage calls for missing sizing and y+h overflow."""
    issues = []
    pos = 0
    call_num = 0
    while True:
        m = re.search(r"addImage\s*\(\s*\{", ts_code[pos:])
        if not m:
            break
        call_num += 1
        brace_start = pos + m.end() - 1
        depth, end = 0, brace_start
        for i, c in enumerate(ts_code[brace_start:]):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = brace_start + i + 1
                    break
        content = ts_code[brace_start:end]
        pos = pos + m.start() + 1

        if "sizing" not in content:
            issues.append(
                f"addImage #{call_num}: missing `sizing` — image will be stretched. "
                "Add: sizing: { type: 'contain', w: <same as w>, h: <same as h> }"
            )

        # Strip nested objects (e.g. sizing:{...}) before extracting outer y/h
        outer = re.sub(r"\{[^{}]*\}", "", content)
        y_m = re.search(r"\by\s*:\s*([\d.]+)", outer)
        h_m = re.search(r"\bh\s*:\s*([\d.]+)", outer)
        if y_m and h_m:
            y, h = float(y_m.group(1)), float(h_m.group(1))
            if y + h > 5.5:
                issues.append(
                    f"addImage #{call_num}: y({y}) + h({h}) = {y + h:.2f}\" > 5.5\" — "
                    "image overflows slide. Reduce h or move y up."
                )

    return issues


def slide_creator_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    analysis = state.get("analysis") or {}
    if not isinstance(analysis, dict):
        analysis = {}
    user_request = state["messages"][-1].content if state.get("messages") else ""

    system = _SYSTEMS.get(lang, _SYSTEMS["vi"]) + lbl(lang, "lang_note")
    slide_outline = analysis.get("slide_outline")

    # Remove image paths that don't exist on disk to avoid PptxGenJS ENOENT errors
    if isinstance(slide_outline, dict):
        from pathlib import Path as _Path
        for section in slide_outline.get("sections", []):
            section["images"] = [
                p for p in section.get("images", [])
                if _Path(p).exists()
            ]

    if slide_outline:
        outline_text = json.dumps(slide_outline, ensure_ascii=False, indent=2)
        user_msg = (
            f"{lbl(lang, 'request')}: {user_request}\n\n"
            f"{lbl(lang, 'slide_outline')}:\n{outline_text}"
        )
    else:
        input_text = json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else state.get("summary", "")
        user_msg = (
            f"{lbl(lang, 'request')}: {user_request}\n\n"
            f"{lbl(lang, 'analysis_result')}:\n{input_text}"
        )

    @tool
    def load_skill_content(slug: str) -> str:
        """Load the full SKILL.md content for any skill by its slug.
        Useful for reading detailed design rules, API usage, or helper references.
        slug: skill name, e.g. 'pptx-slides', 'slide-creation'"""
        return activate_skill(slug, lang)

    tools = [load_skill_content, read_reference, read_script_file]
    llm_with_tools = _llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=user_msg),
    ]

    _val_retries = 0
    for _ in range(MAX_ITERATIONS):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            raw_check = (response.content or "").strip()
            ts_m = re.search(r"```(?:typescript|ts)\n(.*?)```", raw_check, re.DOTALL)
            if ts_m and _val_retries < 2:
                issues = _validate_ts_images(ts_m.group(1))
                if issues:
                    _val_retries += 1
                    feedback = (
                        "VALIDATION ERRORS — fix all issues then output the corrected code:\n"
                        + "\n".join(f"- {e}" for e in issues)
                    )
                    messages.append(HumanMessage(content=feedback))
                    continue
            break

        for tc in response.tool_calls:
            fn = tool_map.get(tc["name"])
            result = fn.invoke(tc["args"]) if fn else f"Tool '{tc['name']}' not found."
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    raw = (messages[-1].content or "").strip()

    # Extract TypeScript code block
    ts_match = re.search(r"```(?:typescript|ts)\n(.*?)```", raw, re.DOTALL)
    if ts_match:
        ts_code = ts_match.group(1).strip()
        slide_path = run_ts_script(ts_code)
        return {"slide_path": slide_path}

    # Fallback: try parsing as JSON deck spec (old format)
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
    cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    try:
        deck = json.loads(cleaned)
        if isinstance(deck, dict) and "slides" in deck:
            slide_path = create_pptx(deck)
            return {"slide_path": slide_path}
        elif isinstance(deck, list):
            theme = (slide_outline or {}).get("theme", "cleanCorporate") if isinstance(slide_outline, dict) else "cleanCorporate"
            slide_path = create_pptx({"theme": theme, "slides": deck})
            return {"slide_path": slide_path}
    except Exception:
        pass

    # Last resort: minimal fallback deck
    theme = (slide_outline or {}).get("theme", "cleanCorporate") if isinstance(slide_outline, dict) else "cleanCorporate"
    slide_path = create_pptx({
        "theme": theme,
        "slides": [
            {"layout": "cover", "title": lbl(lang, "slide_fallback_title")},
            {"layout": "bullets", "title": lbl(lang, "slide_fallback_content"), "bullets": [raw[:200]]},
        ],
    })
    return {"slide_path": slide_path}
