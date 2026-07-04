import json
from pathlib import Path

BASE = Path(__file__).parent.parent


def parse_json_response(content: str):
    """Parse JSON từ LLM response, tự động bỏ markdown code block nếu có."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
    return json.loads(content.strip())


def load_prompt(agent_name: str, lang: str = "vi") -> str:
    base = BASE / "prompts"
    if lang != "vi":
        p = base / f"{agent_name}.{lang}.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
    p = base / f"{agent_name}.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_skill(skill_name: str, lang: str = "vi") -> str:
    base = BASE / "skills" / skill_name
    if lang != "vi":
        p = base / f"SKILL.{lang}.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
    p = base / "SKILL.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_system_prompt(*parts: str) -> str:
    return "\n\n---\n\n".join(p for p in parts if p)
