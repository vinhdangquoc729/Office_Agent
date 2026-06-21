import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from agents import load_prompt, build_system_prompt
from graph.state import DocQAState
from tools.file_readers import read_pdf_pages, read_pdf_pages_detailed, get_pdf_page_count
from tools.analysis import run_python_subprocess
from tools.skill_loader import build_skill_catalog, activate_skill
from agents.helpers import pdf_helper

MAX_ITERATIONS = 15

_SKILL_CATALOG = build_skill_catalog()
_BASE_PROMPT = load_prompt("analyst")
_llm = ChatOpenAI(model="gpt-4o", temperature=0)

_SELECT_PROMPT = """\
Bạn là skill selector. Dựa vào file type và yêu cầu người dùng, chọn các skill phù hợp.

{catalog}

Trả về JSON array các slug cần kích hoạt. Chỉ trả JSON, không giải thích.
Ví dụ: ["excel-analysis", "data-qa"]
"""


# --- Tool definitions (module-level, file_path truyền tường minh) ---

@tool
def pdf_get_page_count(file_path: str) -> int:
    """Lấy tổng số trang của file PDF."""
    return get_pdf_page_count(file_path)


@tool
def pdf_summarize_pages(file_path: str, page_start: int, page_end: int) -> str:
    """Nhờ PDF helper tóm tắt nội dung từng trang trong khoảng [page_start, page_end] (1-indexed, inclusive).
    Mỗi trang trả về: page_number, summary, images (tọa độ).
    Nên gọi với batch 5-7 trang mỗi lần."""
    result = pdf_helper.run(file_path, page_start, page_end)
    return json.dumps(result, ensure_ascii=False)


@tool
def pdf_read_pages(file_path: str, page_start: int, page_end: int) -> str:
    """Đọc nội dung các trang PDF: text, bảng, danh sách ảnh (vị trí + kích thước), annotations.
    Dùng khi cần đọc kỹ nội dung trang sau khi đã biết trang nào liên quan."""
    result = read_pdf_pages(file_path, page_start, page_end)
    return json.dumps(result, ensure_ascii=False)


@tool
def pdf_read_pages_detailed(file_path: str, page_start: int, page_end: int) -> str:
    """Đọc chi tiết vector PDF: chars với font/size/màu/tọa độ, lines, rects.
    Chỉ dùng khi thật sự cần biết vị trí chính xác các phần tử (ví dụ: phân tích layout, detect heading, xác định vị trí hình ảnh cụ thể). Nặng hơn pdf_read_pages, hạn chế dùng."""
    result = read_pdf_pages_detailed(file_path, page_start, page_end)
    return json.dumps(result, ensure_ascii=False)


@tool
def pdf_rag_search(file_path: str, query: str) -> str:
    """Tìm kiếm ngữ nghĩa trong tài liệu PDF, trả về các đoạn văn bản liên quan nhất kèm số trang.
    Lần đầu gọi sẽ index toàn bộ tài liệu (chậm hơn), các lần sau tìm kiếm nhanh.
    Dùng khi: cần tìm thông tin nhưng không biết ở trang nào, hoặc tài liệu dài > 30 trang."""
    from tools.rag_store import rag_search, index_pdf, is_indexed
    if not is_indexed(file_path):
        pages = read_pdf_pages(file_path, 1, get_pdf_page_count(file_path))
        index_pdf(file_path, pages)
    results = rag_search(file_path, query)
    if not results:
        return "Không tìm thấy kết quả phù hợp."
    return json.dumps(results, ensure_ascii=False)


@tool
def pdf_extract_images(file_path: str, page_start: int, page_end: int) -> str:
    """Trích xuất ảnh từ các trang PDF chỉ định, lưu vào thư mục riêng.
    Trang đã extract trước đó sẽ bị bỏ qua (không extract lại).
    Trả về manifest JSON: danh sách tất cả ảnh đã extract, gồm filename, path, page, tọa độ, kích thước.
    Dùng khi cần đưa ảnh vào slide hoặc xem ảnh nào có trong tài liệu."""
    from tools.image_extractor import extract_images
    manifest = extract_images(file_path, page_start, page_end)
    if not manifest:
        return "Không tìm thấy ảnh nào trong khoảng trang đã chỉ định."
    return json.dumps(manifest, ensure_ascii=False)


@tool
def pdf_annotate_images(file_path: str, annotations: list[dict]) -> str:
    """Ghi mô tả ('about') cho các ảnh vào manifest. Gọi sau khi đã đọc nội dung trang để suy luận ảnh là gì.
    annotations: list các dict {"filename": "page005_img01.png", "about": "mô tả ngắn về ảnh này"}.
    Trả về số ảnh đã được cập nhật."""
    from tools.image_extractor import annotate_images
    updated = annotate_images(file_path, annotations)
    return f"Đã cập nhật 'about' cho {updated} ảnh."


@tool
def run_code(code: str) -> str:
    """Chạy Python code (pandas, numpy) để tính toán, thống kê dữ liệu.
    Kết quả in ra stdout sẽ được trả về. Không dùng cho I/O file."""
    return run_python_subprocess(code)


_PDF_TOOLS = [pdf_get_page_count, pdf_rag_search, pdf_summarize_pages, pdf_read_pages, pdf_read_pages_detailed, pdf_extract_images, pdf_annotate_images, run_code]
_GENERAL_TOOLS = [run_code]


def analyst_node(state: DocQAState) -> dict:
    file_type = state.get("file_type", "")
    file_path = state.get("file_path", "")
    file_content = state.get("file_content", "")
    user_request = state["messages"][-1].content if state.get("messages") else ""

    # Activation: chọn skill cần dùng
    selector_resp = _llm.invoke([
        {"role": "system", "content": _SELECT_PROMPT.format(catalog=_SKILL_CATALOG)},
        {"role": "user",   "content": f"file_type: {file_type}\nYêu cầu: {user_request}"},
    ])
    try:
        selected = json.loads(selector_resp.content)
        if not isinstance(selected, list):
            selected = []
    except Exception:
        selected = []

    skill_contents = [activate_skill(slug) for slug in selected if slug]
    system = build_system_prompt(_BASE_PROMPT, *skill_contents)

    tools = _PDF_TOOLS if file_type == "pdf" else _GENERAL_TOOLS
    llm_with_tools = _llm.bind_tools(tools)

    slide_reminder = ""
    if "slide-content" in selected:
        slide_reminder = (
            "\n\nNHIỆM VỤ BẮT BUỘC: Yêu cầu này là TẠO SLIDE. "
            "Trường 'slides' trong output JSON PHẢI được điền đầy đủ — đây là output chính, không phải tuỳ chọn. "
            "Trước khi kết thúc, kiểm tra lại: 'slides' có phải là array không rỗng không?"
        )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=(
            f"file_path: {file_path}\n"
            f"file_type: {file_type}\n"
            f"Yêu cầu: {user_request}{slide_reminder}\n\n"
            f"Thông tin tài liệu (metadata + preview):\n{file_content}"
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
            result = fn.invoke(tc["args"]) if fn else f"Tool '{tc['name']}' không tồn tại."
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    final = messages[-1].content or ""
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", final.strip())
    cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    try:
        analysis = json.loads(cleaned)
    except Exception:
        analysis = {"prose_summary": final}

    return {"analysis": analysis}
