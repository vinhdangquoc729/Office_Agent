import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def _parse_frontmatter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    result = {}
    for line in match.group(1).splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            result[k.strip()] = v.strip()
    return result


def list_skills() -> list[dict]:
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        slug = skill_md.parent.name
        skills.append({
            "slug": slug,
            "name": meta.get("name", slug),
            "description": meta.get("description", ""),
        })
    return skills


def activate_skill(slug: str) -> str:
    skill_md = SKILLS_DIR / slug / "SKILL.md"
    if not skill_md.exists():
        return ""
    return skill_md.read_text(encoding="utf-8")


def build_skill_catalog() -> str:
    lines = ["## Available Skills (Discovery)\n"]
    for s in list_skills():
        lines.append(f'- `{s["slug"]}`: {s["description"]}')
    return "\n".join(lines)
