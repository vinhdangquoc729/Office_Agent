import json
import re
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from agents import load_prompt, build_system_prompt, parse_json_response
from agents.i18n import lbl
from graph.state import DocQAState
from tools.file_readers import read_pdf_pages, read_pdf_pages_detailed, get_pdf_page_count
from tools.analysis import run_python_subprocess
from tools.skill_loader import build_skill_catalog, activate_skill, read_skill_reference
from agents.helpers import pdf_helper

MAX_ITERATIONS = 15

_BASE_PROMPTS: dict[str, str] = {lang: load_prompt("analyst", lang) for lang in ("vi", "en")}
_SKILL_CATALOGS: dict[str, str] = {lang: build_skill_catalog(lang) for lang in ("vi", "en")}
_llm = ChatOpenAI(model="gpt-4o", temperature=0)



@tool
def read_reference(skill: str, filename: str) -> str:
    """Đọc file tham khảo trong references/ của một skill đang active.
    Dùng khi cần xem template chi tiết, ví dụ code, hoặc hướng dẫn bổ sung.
    skill: tên skill (ví dụ 'excel-analysis')
    filename: tên file (ví dụ 'chart_templates.md')"""
    return read_skill_reference(skill, filename)


def _extract_file_metadata(file_content: str) -> tuple[list, list, dict, list]:
    """Trả về (file_paths_posix, files_metadata, sheets_columns_0, sheet_names_0).

    files_metadata: list[dict] với {suggested_header_row, sheets_columns} per file.
    """
    files_metadata: list[dict] = []
    suggested_header_row_0 = 0
    sheets_columns_0: dict = {}
    sheet_names_0: list = []

    try:
        fc = json.loads(file_content) if file_content else {}
        if not isinstance(fc, dict):
            return files_metadata, suggested_header_row_0, sheets_columns_0, sheet_names_0

        if "files" in fc:
            # Multi-file format
            for f in fc["files"]:
                meta = {
                    "suggested_header_row": f.get("suggested_header_row") or 0,
                    "sheets_columns": f.get("sheets_columns") or {},
                }
                files_metadata.append(meta)
            if files_metadata:
                suggested_header_row_0 = files_metadata[0]["suggested_header_row"]
                sheets_columns_0 = files_metadata[0]["sheets_columns"]
                sheet_names_0 = list(sheets_columns_0.keys())
        else:
            # Single-file format (backward compat)
            meta = {
                "suggested_header_row": fc.get("suggested_header_row") or 0,
                "sheets_columns": fc.get("sheets_columns") or {},
            }
            files_metadata = [meta]
            suggested_header_row_0 = meta["suggested_header_row"]
            sheets_columns_0 = meta["sheets_columns"]
            sheet_names_0 = list(sheets_columns_0.keys())
    except Exception:
        pass

    return files_metadata, suggested_header_row_0, sheets_columns_0, sheet_names_0


def _build_file_list_context(file_paths: list, file_content: str, file_names: list | None = None, lang: str = "vi") -> str:
    try:
        fc = json.loads(file_content) if file_content else {}
    except Exception:
        fc = {}

    lines = [lbl(lang, "file_list_header")]
    if "files" in fc:
        for f in fc["files"]:
            summary = (f.get("content") or "")[:200].replace("\n", " ")
            lines.append(f"  [{f['index']}] {f['name']} ({f['type']}) — {summary}...")
    else:
        if file_names:
            name = file_names[0]
        elif file_paths:
            name = Path(file_paths[0]).name
        else:
            name = "file"
        summary = (fc.get("content") or file_content or "")[:200].replace("\n", " ")
        lines.append(f"  [0] {name} — {summary}...")
    return "\n".join(lines)


def analyst_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    file_type = state.get("file_type", "")
    file_content = state.get("file_content", "")
    user_request = state["messages"][-1].content if state.get("messages") else ""

    file_paths_state: list = state.get("file_paths") or (
        [state["file_path"]] if state.get("file_path") else []
    )
    file_path = file_paths_state[0] if file_paths_state else ""

    files_metadata, suggested_header_row, sheets_columns, sheet_names = \
        _extract_file_metadata(file_content)

    # --- PDF tools (closures capturing file_paths_state) ---

    @tool
    def pdf_get_page_count(file_index: int = 0) -> int:
        """Lấy tổng số trang của file PDF.
        file_index: chỉ số file trong danh sách (mặc định 0)."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        return get_pdf_page_count(path)

    @tool
    def pdf_summarize_pages(file_index: int, page_start: int, page_end: int) -> str:
        """Nhờ PDF helper tóm tắt nội dung từng trang trong khoảng [page_start, page_end] (1-indexed, inclusive).
        file_index: chỉ số file. Nên gọi với batch 5-7 trang mỗi lần."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        result = pdf_helper.run(path, page_start, page_end, lang)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def pdf_read_pages(file_index: int, page_start: int, page_end: int) -> str:
        """Đọc nội dung các trang PDF: text, bảng, danh sách ảnh, annotations.
        file_index: chỉ số file. Dùng khi cần đọc kỹ nội dung trang cụ thể."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        result = read_pdf_pages(path, page_start, page_end)
        for page in result:
            text = page.get("text", "")
            clean = re.sub(r"[^\w]", "", text, flags=re.UNICODE)
            words = text.split()
            if (len(clean) < 100 or len(words) < 20) and page.get("images"):
                page["_ocr_hint"] = lbl(
                    lang, "ocr_hint",
                    page=page["page_number"], chars=len(clean), words=len(words),
                    n=len(page["images"]), idx=file_index,
                )
        return json.dumps(result, ensure_ascii=False)

    @tool
    def pdf_read_pages_detailed(file_index: int, page_start: int, page_end: int) -> str:
        """Đọc chi tiết vector PDF: chars với font/size/màu/tọa độ, lines, rects.
        file_index: chỉ số file. Chỉ dùng khi cần vị trí chính xác các phần tử."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        result = read_pdf_pages_detailed(path, page_start, page_end)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def pdf_rag_search(file_index: int, query: str) -> str:
        """Tìm kiếm ngữ nghĩa trong tài liệu PDF, trả về đoạn liên quan nhất kèm số trang.
        file_index: chỉ số file. Dùng khi không biết thông tin ở trang nào."""
        from tools.rag_store import rag_search, index_pdf, is_indexed
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        if not is_indexed(path):
            pages = read_pdf_pages(path, 1, get_pdf_page_count(path))
            index_pdf(path, pages)
        results = rag_search(path, query)
        if not results:
            return lbl(lang, "no_search_results")
        return json.dumps(results, ensure_ascii=False)

    @tool
    def pdf_extract_images(file_index: int, page_start: int, page_end: int) -> str:
        """Trích xuất ảnh từ các trang PDF chỉ định.
        file_index: chỉ số file. Trả về manifest JSON: filename, path, page, tọa độ, kích thước."""
        from tools.image_extractor import extract_images
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        manifest = extract_images(path, page_start, page_end)
        if not manifest:
            return lbl(lang, "no_images_found")
        return json.dumps(manifest, ensure_ascii=False)

    @tool
    def pdf_annotate_images(file_index: int, annotations: list[dict]) -> str:
        """Ghi mô tả ('about') cho các ảnh vào manifest.
        file_index: chỉ số file.
        annotations: list dict {"filename": "page005_img01.png", "about": "mô tả"}."""
        from tools.image_extractor import annotate_images
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        updated = annotate_images(path, annotations)
        return lbl(lang, "updated_about", n=updated)

    @tool
    def pdf_ocr_page(file_index: int, page_number: int) -> str:
        """OCR trang PDF bằng EasyOCR, trả về text thuần đã ghép lại theo thứ tự từ trên xuống.
        Dùng khi pdf_read_pages có _ocr_hint hoặc text sơ sài mà trang có ảnh.
        file_index: chỉ số file. page_number: số trang (1-indexed)."""
        from tools.ocr import ocr_page
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        blocks = ocr_page(path, page_number)
        if not blocks:
            return lbl(lang, "no_ocr_text")
        sorted_blocks = sorted(blocks, key=lambda b: -b["y1"])
        return "\n".join(b["text"] for b in sorted_blocks if b["text"].strip())

    @tool
    def pdf_ocr_page_detailed(file_index: int, page_number: int) -> str:
        """OCR trang PDF bằng EasyOCR, trả về list blocks đầy đủ với tọa độ PDF points.
        Mỗi block: {text, confidence, x0, y0, x1, y1}.
        Dùng khi cần biết vị trí chính xác của text trong trang (layout, caption, vùng cụ thể).
        file_index: chỉ số file. page_number: số trang (1-indexed)."""
        from tools.ocr import ocr_page
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        blocks = ocr_page(path, page_number)
        if not blocks:
            return lbl(lang, "no_ocr_text")
        return json.dumps(blocks, ensure_ascii=False)

    # --- run_code closure ---

    @tool
    def run_code(code: str) -> str:
        """Chạy Python code (pandas, numpy) để tính toán, thống kê dữ liệu.
        QUAN TRỌNG:
        1. Mỗi lần gọi là một subprocess độc lập — biến từ lần gọi trước KHÔNG tồn tại.
        2. Phải dùng print() để xuất kết quả — expression cuối KHÔNG tự động hiển thị.
        Các biến được inject sẵn:
          - file_paths        : list đường dẫn tất cả file (posix), dùng file_paths[index]
          - file_path         : = file_paths[0] (file đầu tiên, backward compat)
          - files_metadata    : list dict {suggested_header_row, sheets_columns} per file
          - suggested_header_row : header row của file_paths[0]
          - sheet_names       : list tên sheet của file_paths[0]
          - sheets_columns    : dict {sheet: [cols]} của file_paths[0]
          - output_dir        : thư mục lưu chart
        Ví dụ:
          import pandas as pd
          df = pd.read_excel(file_path, sheet_name=sheet_names[0], header=suggested_header_row)
          # File thứ 2:
          df2 = pd.read_excel(file_paths[1], header=files_metadata[1]['suggested_header_row'])"""
        all_posix = [p.replace("\\", "/") for p in file_paths_state]
        fp_posix = all_posix[0] if all_posix else ""
        uploads_dir = "/".join(fp_posix.split("/")[:-1])
        output_dir_str = f"{uploads_dir}/charts"
        output_path = Path(output_dir_str)
        output_path.mkdir(exist_ok=True)

        before_pngs = set(output_path.glob("*.png")) if output_path.is_dir() else set()

        preamble = (
            f"file_paths = {repr(all_posix)}\n"
            f"file_path = file_paths[0]\n"
            f"files_metadata = {repr(files_metadata)}\n"
            f"suggested_header_row = {suggested_header_row}\n"
            f"sheet_names = {repr(sheet_names)}\n"
            f"sheets_columns = {repr(sheets_columns)}\n"
            f"output_dir = '{output_dir_str}'\n"
        )
        result = run_python_subprocess(preamble + "\n" + code)

        after_pngs = set(output_path.glob("*.png")) if output_path.is_dir() else set()
        ts = int(time.time())
        for png in sorted(after_pngs - before_pngs):
            already_reported = any(str(png) in line for line in result.splitlines())
            if already_reported:
                continue
            if not re.search(r"_\d{9,}\.", png.name):
                stamped = png.with_name(f"{png.stem}_{ts}{png.suffix}")
                png.rename(stamped)
                png = stamped
            result = result.rstrip("\n") + f"\nchart_saved:{png}"

        return result

    # --- Skill selection ---
    catalog = _SKILL_CATALOGS.get(lang, _SKILL_CATALOGS["vi"])
    selector_resp = _llm.invoke([
        {"role": "system", "content": lbl(lang, "select_prompt", catalog=catalog)},
        {"role": "user",   "content": f"file_type: {file_type}\n{lbl(lang, 'request')}: {user_request}"},
    ])
    try:
        selected = parse_json_response(selector_resp.content)
        if not isinstance(selected, list):
            selected = []
    except Exception:
        selected = []

    skill_contents = [activate_skill(slug, lang) for slug in selected if slug]
    base = _BASE_PROMPTS.get(lang, _BASE_PROMPTS["vi"])
    system = build_system_prompt(base, *skill_contents)

    _pdf_tools = [pdf_get_page_count, pdf_rag_search, pdf_summarize_pages,
                  pdf_read_pages, pdf_read_pages_detailed, pdf_extract_images, pdf_annotate_images,
                  pdf_ocr_page, pdf_ocr_page_detailed]
    has_pdf = any(Path(p).suffix.lower() == ".pdf" for p in file_paths_state)
    tools = [*_pdf_tools, read_reference, run_code] if has_pdf else [read_reference, run_code]
    llm_with_tools = _llm.bind_tools(tools)

    slide_reminder = lbl(lang, "slide_mandatory") if "slide-content" in selected else ""

    file_names_state: list = state.get("file_names") or []
    file_list_ctx = _build_file_list_context(file_paths_state, file_content, file_names_state, lang)

    # Conversation history: last 3 Q&A pairs (excluding current message)
    all_msgs = state.get("messages", [])
    history_turns = all_msgs[:-1] if len(all_msgs) > 1 else []
    history_ctx = ""
    if history_turns:
        lines = []
        for m in history_turns[-6:]:
            role = lbl(lang, "user_role") if isinstance(m, HumanMessage) else lbl(lang, "assistant_role")
            text = (m.content or "")[:600]
            lines.append(f"{role}: {text}")
        history_ctx = f"\n\n{lbl(lang, 'history_header')}\n" + "\n".join(lines) + "\n"

    messages = [
        SystemMessage(content=system + lbl(lang, "lang_note")),
        HumanMessage(content=(
            f"{file_list_ctx}"
            f"{history_ctx}\n"
            f"{lbl(lang, 'current_request')}: {user_request}{slide_reminder}\n\n"
            f"{lbl(lang, 'document_content')}:\n{file_content}"
        )),
    ]

    tool_map = {t.name: t for t in tools}
    for _ in range(MAX_ITERATIONS):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            fn = tool_map.get(tc["name"])
            result = fn.invoke(tc["args"]) if fn else lbl(lang, "tool_not_found", name=tc["name"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    chart_paths = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            for line in msg.content.splitlines():
                if line.startswith("chart_saved:"):
                    chart_paths.append(line[len("chart_saved:"):].strip())

    final = messages[-1].content or ""
    try:
        analysis = parse_json_response(final)
    except Exception:
        analysis = {"prose_summary": final}

    return {"analysis": analysis, "chart_paths": chart_paths}
