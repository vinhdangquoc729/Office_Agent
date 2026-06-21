import json

from langchain_openai import ChatOpenAI

from agents import load_prompt, build_system_prompt
from tools.file_readers import read_pdf_pages

_SYSTEM = build_system_prompt(load_prompt("pdf_helper"))
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def run(file_path: str, page_start: int, page_end: int) -> list[dict]:
    """Đọc các trang PDF, tóm tắt bằng LLM, trả về JSON với summary và tọa độ ảnh.
    Analyst nên gọi với batch 5-7 trang mỗi lần."""
    pages = read_pdf_pages(file_path, page_start, page_end)
    if not pages:
        return []

    pages_text = []
    for page in pages:
        text = page["text"].strip()
        entry = f"=== Trang {page['page_number']} ==="
        if not text:
            entry += "\n[Không có text — trang hình ảnh hoặc scan]"
        else:
            entry += f"\n{text[:1500]}"
            if page["tables"]:
                entry += "\n[Bảng]:\n" + "\n".join(page["tables"])
        if page["images"]:
            entry += f"\n[Trang có {len(page['images'])} hình ảnh nhúng]"
        pages_text.append(entry)

    user_content = (
        "Tóm tắt từng trang dưới đây. "
        "Trả về JSON array, mỗi phần tử gồm page_number (int) và summary (string).\n\n"
        + "\n\n".join(pages_text)
    )

    response = _llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": user_content},
    ])

    try:
        summaries = json.loads(response.content)
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
