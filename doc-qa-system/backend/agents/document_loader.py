import json
import re
from pathlib import Path

from langchain_openai import ChatOpenAI

from agents import load_prompt, load_skill, build_system_prompt
from agents.i18n import lbl
from graph.state import DocQAState
from tools.file_readers import read_file, read_pdf_meta, read_tabular_meta

_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(
        load_prompt("document_loader", lang),
        load_skill("pdf-extraction", lang),
        load_skill("excel-analysis", lang),
    )
    for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o", temperature=0)


def _load_one(file_path: str, lang: str = "vi") -> dict:
    """Load 1 file, trả về dict {file_type, content, suggested_header_row, sheets_columns}."""
    ext = Path(file_path).suffix.lower()

    try:
        if ext == ".pdf":
            pdf_info = read_pdf_meta(file_path)
            file_type = "pdf"
            user_content = json.dumps(pdf_info, ensure_ascii=False)
        elif ext in (".xlsx", ".xls", ".csv"):
            meta = read_tabular_meta(file_path)
            file_type = "xlsx"
            user_content = json.dumps(meta, ensure_ascii=False)
        else:
            raw_content, file_type = read_file(file_path)
            user_content = f"Loại file: {file_type}\n\nNội dung:\n{raw_content[:8000]}"
    except Exception as e:
        return {"error": str(e)}

    system = _SYSTEMS.get(lang, _SYSTEMS["vi"])
    response = _llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ])

    suggested_header_row = 0
    sheets_columns: dict = {}
    try:
        raw = response.content.strip()
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()
        result = json.loads(raw)
        cleaned = result.get("cleaned_content", response.content)
        suggested_header_row = result.get("suggested_header_row") or 0
        if ext in (".xlsx", ".xls", ".csv"):
            import pandas as pd
            xl = pd.ExcelFile(file_path)
            for name in xl.sheet_names:
                df = xl.parse(name, header=suggested_header_row)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [" > ".join(str(c) for c in col).strip() for col in df.columns]
                sheets_columns[name] = [str(c) for c in df.columns]
    except Exception:
        cleaned = response.content

    return {
        "file_type": file_type,
        "content": cleaned,
        "suggested_header_row": suggested_header_row,
        "sheets_columns": sheets_columns,
    }


def document_loader_node(state: DocQAState) -> dict:
    if state.get("file_content"):
        return {}

    file_paths: list = state.get("file_paths") or (
        [state["file_path"]] if state.get("file_path") else []
    )
    lang = state.get("lang", "vi")
    if not file_paths:
        return {"error": lbl(lang, "no_files"), "file_content": ""}

    # Single file: giữ format cũ để backward compat
    if len(file_paths) == 1:
        result = _load_one(file_paths[0], lang)
        if "error" in result:
            return {"error": result["error"], "file_content": ""}
        file_type = result["file_type"]
        ext = Path(file_paths[0]).suffix.lower()
        if ext in (".xlsx", ".xls", ".csv"):
            out = {
                "content": result["content"],
                "suggested_header_row": result["suggested_header_row"],
                "sheets_columns": result["sheets_columns"],
            }
            file_content = json.dumps(out, ensure_ascii=False)
        else:
            file_content = result["content"]
        return {"file_content": file_content, "file_type": file_type, "error": ""}

    # Multi-file: format mới
    file_names = state.get("file_names") or []
    files_data = []
    primary_type = None
    for i, fp in enumerate(file_paths):
        result = _load_one(fp, lang)
        if "error" in result:
            return {"error": lbl(lang, "file_read_error", name=Path(fp).name, error=result["error"]), "file_content": ""}
        if primary_type is None:
            primary_type = result["file_type"]
        files_data.append({
            "index": i,
            "name": file_names[i] if i < len(file_names) else Path(fp).name,
            "type": result["file_type"],
            "content": result["content"],
            "suggested_header_row": result["suggested_header_row"],
            "sheets_columns": result["sheets_columns"],
        })

    file_content = json.dumps({"files": files_data}, ensure_ascii=False)
    return {"file_content": file_content, "file_type": primary_type, "error": ""}
