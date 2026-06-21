import json
from pathlib import Path

from langchain_openai import ChatOpenAI

from agents import load_prompt, load_skill, build_system_prompt
from graph.state import DocQAState
from tools.file_readers import read_file, read_pdf_meta

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
        result = json.loads(response.content)
        cleaned = result.get("cleaned_content", response.content)
    except Exception:
        cleaned = response.content

    return {
        "file_content": cleaned,
        "file_type": file_type,
        "error": "",
    }
