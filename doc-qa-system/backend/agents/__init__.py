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


def load_prompt(agent_name: str) -> str:
    path = BASE / "prompts" / f"{agent_name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_skill(skill_name: str) -> str:
    path = BASE / "skills" / skill_name / "SKILL.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_system_prompt(*parts: str) -> str:
    return "\n\n---\n\n".join(p for p in parts if p)
