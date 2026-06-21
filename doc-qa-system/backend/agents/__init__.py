from pathlib import Path

BASE = Path(__file__).parent.parent


def load_prompt(agent_name: str) -> str:
    path = BASE / "prompts" / f"{agent_name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_skill(skill_name: str) -> str:
    path = BASE / "skills" / skill_name / "SKILL.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_system_prompt(*parts: str) -> str:
    return "\n\n---\n\n".join(p for p in parts if p)
