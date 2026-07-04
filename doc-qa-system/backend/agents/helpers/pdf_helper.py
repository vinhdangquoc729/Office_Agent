import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt, parse_json_response
from tools.file_readers import read_pdf_pages

_SYSTEMS: dict[str, str] = {
    lang: build_system_prompt(load_prompt("pdf_helper", lang))
    for lang in ("vi", "en")
}
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def run(file_path: str, page_start: int, page_end: int, lang: str = "vi") -> list[dict]:
    """Đọc các trang PDF, tóm tắt bằng LLM, trả về JSON với summary và tọa độ ảnh.
    Analyst nên gọi với batch 5-7 trang mỗi lần."""
    pages = read_pdf_pages(file_path, page_start, page_end)
    if not pages:
        return []

    _page_label = "Page" if lang == "en" else "Trang"
    _no_text = "[No text — image-only or scanned page]" if lang == "en" else "[Không có text — trang hình ảnh hoặc scan]"
    _table_label = "[Tables]:" if lang == "en" else "[Bảng]:"
    _images_label = (lambda n: f"[Page contains {n} embedded image(s)]") if lang == "en" else (lambda n: f"[Trang có {n} hình ảnh nhúng]")
    _user_instruction = (
        "Summarize each page below. Return a JSON array where each element has page_number (int) and summary (string).\n\n"
        if lang == "en" else
        "Tóm tắt từng trang dưới đây. Trả về JSON array, mỗi phần tử gồm page_number (int) và summary (string).\n\n"
    )

    pages_text = []
    for page in pages:
        text = page["text"].strip()
        entry = f"=== {_page_label} {page['page_number']} ==="
        if not text:
            entry += f"\n{_no_text}"
        else:
            entry += f"\n{text[:1500]}"
            if page["tables"]:
                entry += f"\n{_table_label}\n" + "\n".join(page["tables"])
        if page["images"]:
            entry += f"\n{_images_label(len(page['images']))}"
        pages_text.append(entry)

    user_content = _user_instruction + "\n\n".join(pages_text)

    system = _SYSTEMS.get(lang, _SYSTEMS["vi"])
    response = _llm.invoke([
        {"role": "system", "content": system},
        {"role": "user",   "content": user_content},
    ])

    try:
        summaries = parse_json_response(response.content)
        if not isinstance(summaries, list):
            raise ValueError
    except Exception:
        summaries = [{"page_number": p["page_number"], "summary": response.content} for p in pages]

    summary_map = {s["page_number"]: s["summary"] for s in summaries}

    return [
        {
            "page_number": page["page_number"],
            "summary": summary_map.get(page["page_number"], ""),
            "images": [
                {"x0": img["x0"], "y0": img["y0"], "x1": img["x1"], "y1": img["y1"]}
                for img in page["images"]
            ],
        }
        for page in pages
    ]
