from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class DocQAState(TypedDict):
    messages: Annotated[list, add_messages]
    file_path: str
    file_type: str        # pdf | xlsx | docx | md
    file_content: str     # raw extracted content từ tool
    analysis: dict        # output của analyst
    summary: str          # output của summarizer
    report_path: str      # đường dẫn file .docx
    slide_path: str       # đường dẫn file .pptx
    chart_paths: list     # đường dẫn các file ảnh biểu đồ sinh ra trong turn này
    request_type: str     # analyze | summarize | report | slide | qa
    need_document: bool   # supervisor quyết định có cần load/reload tài liệu không
    error: str
