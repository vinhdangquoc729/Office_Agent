from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class DocQAState(TypedDict):
    messages: Annotated[list, add_messages]
    file_path: str        # = file_paths[0], giữ cho backward compat
    file_paths: list      # tất cả paths trong conversation
    file_names: list      # tên gốc tương ứng với file_paths
    file_type: str        # type của file_paths[0]
    file_content: str     # raw extracted content từ tool
    analysis: dict        # output của analyst
    summary: str          # output của summarizer
    report_path: str      # đường dẫn file .docx
    slide_path: str       # đường dẫn file .pptx
    chart_paths: list     # đường dẫn các file ảnh biểu đồ sinh ra trong turn này
    request_type: str     # analyze | summarize | report | slide | qa
    need_document: bool   # supervisor quyết định có cần load/reload tài liệu không
    error: str
