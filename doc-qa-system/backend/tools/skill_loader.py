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


def _skill_path(slug: str, lang: str = "vi") -> Path:
    if lang != "vi":
        p = SKILLS_DIR / slug / f"SKILL.{lang}.md"
        if p.exists():
            return p
    return SKILLS_DIR / slug / "SKILL.md"


def list_skills(lang: str = "vi") -> list[dict]:
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        slug = skill_md.parent.name
        path = _skill_path(slug, lang)
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        meta = _parse_frontmatter(text)
        skills.append({
            "slug": slug,
            "name": meta.get("name", slug),
            "description": meta.get("description", ""),
        })
    return skills


def activate_skill(slug: str, lang: str = "vi") -> str:
    path = _skill_path(slug, lang)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_skill_reference(slug: str, filename: str) -> str:
    """Đọc một file trong references/ của skill. Trả về nội dung hoặc thông báo lỗi."""
    ref_path = SKILLS_DIR / slug / "references" / filename
    if not ref_path.exists():
        refs_dir = SKILLS_DIR / slug / "references"
        available = [f.name for f in sorted(refs_dir.glob("*"))] if refs_dir.is_dir() else []
        return f"Không tìm thấy '{filename}'. Có sẵn: {available}"
    return ref_path.read_text(encoding="utf-8")


def read_skill_script(slug: str, filename: str) -> str:
    """Đọc một file trong scripts/ của skill. Trả về nội dung hoặc thông báo lỗi."""
    script_path = SKILLS_DIR / slug / "scripts" / filename
    if not script_path.exists():
        scripts_dir = SKILLS_DIR / slug / "scripts"
        available = [f.name for f in sorted(scripts_dir.glob("*.ts")) if not f.name.startswith("_")]
        if scripts_dir.is_dir() and not available:
            available = [f.name for f in sorted(scripts_dir.iterdir()) if f.is_file() and not f.name.startswith("_") and f.suffix in (".ts", ".js")]
        return f"Không tìm thấy '{filename}'. File .ts có sẵn: {available}"
    return script_path.read_text(encoding="utf-8")


_ANALYST_EXCLUDED = {"pptx-slides", "slide-creation"}


def build_skill_catalog(lang: str = "vi", excluded: set | None = None) -> str:
    if excluded is None:
        excluded = _ANALYST_EXCLUDED
    lines = ["## Available Skills (Discovery)\n"]
    for s in list_skills(lang):
        if s["slug"] in excluded:
            continue
        lines.append(f'- `{s["slug"]}`: {s["description"]}')
    return "\n".join(lines)
