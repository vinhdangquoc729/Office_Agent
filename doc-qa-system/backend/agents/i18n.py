_LABELS = {
    "vi": {
        "user_role": "Người dùng",
        "assistant_role": "Trợ lý",
        "history_header": "Lịch sử hội thoại:",
        "file_list_header": "Danh sách tài liệu (dùng file_index khi gọi tool):",
        "current_request": "Yêu cầu hiện tại",
        "document_content": "Nội dung tài liệu",
        "request": "Yêu cầu",
        "analysis_result": "Kết quả phân tích",
        "summary_content": "Nội dung cần tóm tắt",
        "user_request": "Yêu cầu của người dùng",
        "analysis_info": "Thông tin phân tích",
        "lang_note": "",
        "no_search_results": "Không tìm thấy kết quả phù hợp.",
        "no_images_found": "Không tìm thấy ảnh nào trong khoảng trang đã chỉ định.",
        "updated_about": "Đã cập nhật 'about' cho {n} ảnh.",
        "no_ocr_text": "Không nhận diện được text nào trên trang này.",
        "ocr_hint": (
            "[HINT] Trang {page}: text sơ sài ({chars} ký tự, {words} từ) "
            "nhưng có {n} ảnh — NÊN gọi pdf_ocr_page(file_index={idx}, "
            "page_number={page}) để đọc nội dung trong ảnh."
        ),
        "page_label": "Trang {page}",
        "file_page_label": "{file} trang {page}",
        "sources_label": "Nguồn",
        "no_files": "Không có file được cung cấp.",
        "file_read_error": "Lỗi khi đọc file {name}: {error}",
        "slide_fallback_title": "Báo cáo",
        "slide_fallback_content": "Nội dung",
        "tool_not_found": "Tool '{name}' không tồn tại.",
        "select_prompt": (
            "Bạn là skill selector. Dựa vào file type và yêu cầu người dùng, chọn các skill phù hợp.\n\n"
            "{catalog}\n\n"
            "Trả về JSON array các slug cần kích hoạt. Chỉ trả JSON, không giải thích.\n"
            "Ví dụ: [\"excel-analysis\", \"data-qa\"]"
        ),
        "slide_mandatory": (
            "\n\nNHIỆM VỤ BẮT BUỘC: Yêu cầu này là TẠO SLIDE. "
            "Trường 'slides' trong output JSON PHẢI được điền đầy đủ — đây là output chính, không phải tuỳ chọn. "
            "Trước khi kết thúc, kiểm tra lại: 'slides' có phải là array không rỗng không?"
        ),
    },
    "en": {
        "user_role": "User",
        "assistant_role": "Assistant",
        "history_header": "Conversation history:",
        "file_list_header": "Document list (use file_index when calling tools):",
        "current_request": "Current request",
        "document_content": "Document content",
        "request": "Request",
        "analysis_result": "Analysis result",
        "summary_content": "Content to summarize",
        "user_request": "User request",
        "analysis_info": "Analysis information",
        "lang_note": "\n\nIMPORTANT: Respond in English.",
        "no_search_results": "No matching results found.",
        "no_images_found": "No images found in the specified page range.",
        "updated_about": "Updated 'about' for {n} images.",
        "no_ocr_text": "No text detected on this page.",
        "ocr_hint": (
            "[HINT] Page {page}: sparse text ({chars} chars, {words} words) "
            "but has {n} images — SHOULD call pdf_ocr_page(file_index={idx}, "
            "page_number={page}) to read text in images."
        ),
        "page_label": "Page {page}",
        "file_page_label": "{file} p.{page}",
        "sources_label": "Sources",
        "no_files": "No files provided.",
        "file_read_error": "Error reading file {name}: {error}",
        "slide_fallback_title": "Report",
        "slide_fallback_content": "Content",
        "tool_not_found": "Tool '{name}' not found.",
        "select_prompt": (
            "You are a skill selector. Based on the file type and user request, select appropriate skills.\n\n"
            "{catalog}\n\n"
            "Return a JSON array of slugs to activate. Return JSON only, no explanation.\n"
            "Example: [\"excel-analysis\", \"data-qa\"]"
        ),
        "slide_mandatory": (
            "\n\nMANDATORY TASK: This request is to CREATE SLIDES. "
            "The 'slides' field in the output JSON MUST be fully populated — this is the primary output, not optional. "
            "Before finishing, verify: is 'slides' a non-empty array?"
        ),
    },
}


def lbl(lang: str, key: str, **kwargs) -> str:
    vi = _LABELS["vi"]
    text = _LABELS.get(lang, vi).get(key) or vi.get(key, key)
    for k, v in kwargs.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text
