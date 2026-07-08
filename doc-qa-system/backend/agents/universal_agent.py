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
from tools.file_readers import (
    read_pdf_pages, read_pdf_pages_detailed, get_pdf_page_count,
    read_pdf_tables_custom, extract_pdf_structure,
)
from tools.analysis import run_python_subprocess
from tools.output_writers import write_report_docx, run_ts_script
from tools.skill_loader import build_skill_catalog, activate_skill, read_skill_reference, read_skill_script
from agents.helpers import pdf_helper

MAX_ITERATIONS = 20

_BASE_PROMPTS: dict[str, str] = {lang: load_prompt("universal_agent", lang) for lang in ("vi", "en")}
# Universal agent sees ALL skills including slide-creation and pptx-slides
_SKILL_CATALOGS: dict[str, str] = {
    lang: build_skill_catalog(lang, excluded=set()) for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o", temperature=0)


@tool
def read_reference(skill: str, filename: str) -> str:
    """Read a reference file from a skill's references/ directory.
    skill: skill slug (e.g. 'pptx-slides', 'slide-creation')
    filename: file name (e.g. 'pptxgenjs-helpers.md')"""
    return read_skill_reference(skill, filename)


@tool
def read_script_file(skill: str, filename: str) -> str:
    """Read a TypeScript source file from a skill's scripts/ directory.
    skill: skill slug (e.g. 'pptx-slides')
    filename: file name (e.g. 'theme.ts')"""
    return read_skill_script(skill, filename)


@tool
def get_image_dimensions(path: str) -> str:
    """Get pixel dimensions and aspect ratio of an image file.
    Call this for every image before placing it on a slide.
    Returns JSON: {width, height, aspect_ratio (width/height)}.
    path: absolute path to the image file."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            return json.dumps({"width": w, "height": h, "aspect_ratio": round(w / h, 4)})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _extract_file_metadata(file_content: str) -> tuple[list, int, dict, list]:
    files_metadata: list[dict] = []
    suggested_header_row_0 = 0
    sheets_columns_0: dict = {}
    sheet_names_0: list = []

    try:
        fc = json.loads(file_content) if file_content else {}
        if not isinstance(fc, dict):
            return files_metadata, suggested_header_row_0, sheets_columns_0, sheet_names_0

        if "files" in fc:
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


def universal_agent_node(state: DocQAState) -> dict:
    lang = state.get("lang", "vi")
    file_type = state.get("file_type", "")
    file_content = state.get("file_content", "")
    user_request = state["messages"][-1].content if state.get("messages") else ""

    file_paths_state: list = state.get("file_paths") or (
        [state["file_path"]] if state.get("file_path") else []
    )

    files_metadata, suggested_header_row, sheets_columns, sheet_names = \
        _extract_file_metadata(file_content)

    # --- Output path accumulators ---
    report_path_out: list[str] = []
    slide_path_out: list[str] = []

    # --- Output tools ---

    @tool
    def write_report(markdown_content: str) -> str:
        """Write the final analysis as a formatted .docx report.
        Call when the user explicitly requests a Word report/document.
        markdown_content: full report content in markdown format.
        Returns the absolute file path of the saved .docx."""
        path = write_report_docx(markdown_content)
        report_path_out.append(path)
        return f"report_saved:{path}"

    @tool
    def create_slide(ts_code: str) -> str:
        """Execute TypeScript PptxGenJS code to generate a .pptx presentation.
        Call when the user requests slides or a PowerPoint presentation.
        ts_code: complete TypeScript code (without ```typescript fences).
        Returns the absolute file path of the saved .pptx."""
        path = run_ts_script(ts_code)
        slide_path_out.append(path)
        return f"slide_saved:{path}"

    # --- PDF tools (closures capturing file_paths_state) ---

    @tool
    def pdf_get_page_count(file_index: int = 0) -> int:
        """Get total page count of a PDF file.
        file_index: index in the document list (default 0)."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        return get_pdf_page_count(path)

    @tool
    def pdf_summarize_pages(file_index: int, page_start: int, page_end: int) -> str:
        """Ask PDF helper to summarize pages [page_start, page_end] (1-indexed, inclusive).
        file_index: document index. Call with at most 5-7 pages at a time."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        result = pdf_helper.run(path, page_start, page_end, lang)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def pdf_read_pages(file_index: int, page_start: int, page_end: int) -> str:
        """Read PDF page content: text, tables, image list, annotations.
        file_index: document index. Use when you need to read specific pages in detail."""
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
        """Read PDF vector detail: chars with font/size/color/coordinates, lines, rects.
        file_index: document index. Only use when exact element positions are needed."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        result = read_pdf_pages_detailed(path, page_start, page_end)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def pdf_rag_search(file_index: int, query: str) -> str:
        """Semantic search in PDF, returns most relevant passages with page numbers.
        file_index: document index. Use when you don't know which page has the information."""
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
    def pdf_extract_images(file_index: int, page_start: int = 1, page_end: int = 9999) -> str:
        """Extract images from PDF pages, save to disk, return JSON manifest.
        file_index: document index. page_start/page_end: range (default: all pages).
        Returns: filename, path, page, coordinates, size."""
        from tools.image_extractor import extract_images
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        manifest = extract_images(path, page_start, page_end)
        if not manifest:
            return lbl(lang, "no_images_found")
        return json.dumps(manifest, ensure_ascii=False)

    @tool
    def pdf_annotate_images(file_index: int, annotations: list[dict]) -> str:
        """Write 'about' description for images in the manifest.
        file_index: document index.
        annotations: list of {filename: str, about: str}."""
        from tools.image_extractor import annotate_images
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        updated = annotate_images(path, annotations)
        return lbl(lang, "updated_about", n=updated)

    @tool
    def pdf_ocr_page(file_index: int, page_number: int) -> str:
        """OCR a PDF page using EasyOCR, returns plain text joined top-to-bottom.
        Use when pdf_read_pages shows _ocr_hint or sparse text with images.
        file_index: document index. page_number: 1-indexed."""
        from tools.ocr import ocr_page
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        blocks = ocr_page(path, page_number)
        if not blocks:
            return lbl(lang, "no_ocr_text")
        sorted_blocks = sorted(blocks, key=lambda b: -b["y1"])
        return "\n".join(b["text"] for b in sorted_blocks if b["text"].strip())

    @tool
    def pdf_ocr_page_detailed(file_index: int, page_number: int) -> str:
        """OCR a PDF page, returns full block list with coordinates.
        Each block: {text, confidence, x0, y0, x1, y1}.
        Use when you need exact text positions (layout, captions).
        file_index: document index. page_number: 1-indexed."""
        from tools.ocr import ocr_page
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        blocks = ocr_page(path, page_number)
        if not blocks:
            return lbl(lang, "no_ocr_text")
        return json.dumps(blocks, ensure_ascii=False)

    @tool
    def pdf_read_table_custom(file_index: int, page_number: int, strategy: str) -> str:
        """Re-extract tables from one page with a custom strategy.
        Use when pdf_read_pages returns empty tables but the page has a table.
        strategy: "lines" (needs visible borders) | "text" (word-position based)
        file_index: document index. page_number: 1-indexed."""
        path = file_paths_state[file_index] if file_index < len(file_paths_state) else file_paths_state[0]
        result = read_pdf_tables_custom(path, page_number, strategy)
        return json.dumps(result, ensure_ascii=False)

    # --- run_code closure ---

    @tool
    def run_code(code: str) -> str:
        """Run Python code (pandas, numpy) for computation and statistics.
        IMPORTANT:
        1. Each call is an independent subprocess — variables from previous calls do NOT persist.
        2. Must use print() to output results — final expressions are NOT auto-displayed.
        Pre-injected variables:
          - file_paths: list of all file paths (posix)
          - file_path: = file_paths[0]
          - files_metadata: list of {suggested_header_row, sheets_columns} per file
          - suggested_header_row: header row of file_paths[0]
          - sheet_names: list of sheet names for file_paths[0]
          - sheets_columns: dict {sheet: [cols]} for file_paths[0]
          - output_dir: directory to save charts"""
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

    # --- Skill selection (Progressive Disclosure) ---
    catalog = _SKILL_CATALOGS.get(lang, _SKILL_CATALOGS["vi"])
    selector_resp = _llm.invoke([
        {"role": "system", "content": lbl(lang, "select_prompt", catalog=catalog)},
        {"role": "user", "content": f"file_type: {file_type}\n{lbl(lang, 'request')}: {user_request}"},
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

    _pdf_tools = [
        pdf_get_page_count, pdf_rag_search, pdf_summarize_pages,
        pdf_read_pages, pdf_read_pages_detailed, pdf_extract_images, pdf_annotate_images,
        pdf_ocr_page, pdf_ocr_page_detailed, pdf_read_table_custom,
    ]
    has_pdf = any(Path(p).suffix.lower() == ".pdf" for p in file_paths_state)
    tools = [
        *(_pdf_tools if has_pdf else []),
        run_code, read_reference, read_script_file, get_image_dimensions,
        write_report, create_slide,
    ]
    llm_with_tools = _llm.bind_tools(tools)

    file_names_state: list = state.get("file_names") or []
    file_list_ctx = _build_file_list_context(file_paths_state, file_content, file_names_state, lang)

    # Conversation history: last 3 Q&A pairs
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
            f"{lbl(lang, 'current_request')}: {user_request}\n\n"
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

    # Collect chart paths from tool results
    chart_paths = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            for line in msg.content.splitlines():
                if line.startswith("chart_saved:"):
                    chart_paths.append(line[len("chart_saved:"):].strip())

    final_text = (messages[-1].content or "").strip()

    return {
        "summary": final_text,
        "analysis": {"prose_summary": final_text},
        "report_path": report_path_out[-1] if report_path_out else "",
        "slide_path": slide_path_out[-1] if slide_path_out else "",
        "chart_paths": chart_paths,
    }
