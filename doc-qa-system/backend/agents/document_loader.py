import json
import re
from pathlib import Path

from langchain_openai import ChatOpenAI

from agents import load_prompt, load_skill, build_system_prompt
from graph.state import DocQAState
from tools.file_readers import read_file, read_pdf_meta, read_tabular_meta

_SYSTEM = build_system_prompt(
    load_prompt("document_loader"),
    load_skill("pdf-extraction"),
    load_skill("excel-analysis"),
)
_llm = ChatOpenAI(model="gpt-4o", temperature=0)


def document_loader_node(state: DocQAState) -> dict:
    if state.get("file_content"):
        return {}

    file_path = state.get("file_path", "")
    if not file_path:
        return {"error": "Không có file được cung cấp.", "file_content": ""}

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
        return {"error": str(e), "file_content": ""}

    response = _llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user_content},
    ])

    try:
        raw = response.content.strip()
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()
        result = json.loads(raw)
        cleaned = result.get("cleaned_content", response.content)
        suggested_header_row = result.get("suggested_header_row") or 0
        # Với xlsx/csv: re-read với header đúng từ LLM → inject tên cột thật
        if ext in (".xlsx", ".xls", ".csv"):
            import pandas as pd
            sheets_columns = {}
            xl = pd.ExcelFile(file_path)
            for name in xl.sheet_names:
                df = xl.parse(name, header=suggested_header_row)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [" > ".join(str(c) for c in col).strip() for col in df.columns]
                sheets_columns[name] = [str(c) for c in df.columns]
            out = {
                "content": cleaned,
                "suggested_header_row": suggested_header_row,
                "sheets_columns": sheets_columns,
            }
            cleaned = json.dumps(out, ensure_ascii=False)
    except Exception:
        cleaned = response.content

    return {
        "file_content": cleaned,
        "file_type": file_type,
        "error": "",
    }
