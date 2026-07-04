import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from agents import load_prompt
from graph.graph import graph_app

_guard_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_GUARD_SYSTEM = load_prompt("input_guard")

_BLOCKED_MSG = {
    "vi": "Tin nhắn bị chặn: có dấu hiệu tấn công prompt injection.",
    "en": "Message blocked: potential prompt injection detected.",
}


async def _check_injection(message: str) -> tuple[bool, str]:
    """Returns (is_safe, reason). Fails open on parse error to avoid blocking legitimate users."""
    resp = await _guard_llm.ainvoke([
        {"role": "system", "content": _GUARD_SYSTEM},
        {"role": "user", "content": message},
    ])
    try:
        result = json.loads(resp.content.strip())
        return bool(result.get("safe", True)), result.get("reason", "")
    except Exception:
        return True, ""

router = APIRouter()

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

NODE_LABELS = {
    "vi": {
        "supervisor":      "Đang xác định yêu cầu...",
        "document_loader": "Đang đọc tài liệu...",
        "analyst":         "Đang phân tích nội dung...",
        "response_maker":  "Đang soạn câu trả lời...",
        "summarizer":      "Đang tóm tắt...",
        "reporter":        "Đang tạo báo cáo...",
        "slide_creator":   "Đang tạo slide...",
    },
    "en": {
        "supervisor":      "Analyzing request...",
        "document_loader": "Reading document...",
        "analyst":         "Analyzing content...",
        "response_maker":  "Composing response...",
        "summarizer":      "Summarizing...",
        "reporter":        "Generating report...",
        "slide_creator":   "Creating slides...",
    },
}

TOOL_LABELS = {
    "vi": {
        "pdf_read_pages":          lambda a: f"Đang đọc trang {a.get('page_start')}-{a.get('page_end')}...",
        "pdf_summarize_pages":     lambda a: f"Đang tóm tắt trang {a.get('page_start')}-{a.get('page_end')}...",
        "pdf_ocr_page":            lambda a: f"Đang OCR trang {a.get('page_number')}...",
        "pdf_ocr_page_detailed":   lambda a: f"Đang OCR chi tiết trang {a.get('page_number')}...",
        "pdf_rag_search":          lambda a: "Đang tìm kiếm ngữ nghĩa...",
        "pdf_extract_images":      lambda a: "Đang trích xuất ảnh...",
        "pdf_read_pages_detailed": lambda a: f"Đang đọc chi tiết trang {a.get('page_start')}-{a.get('page_end')}...",
        "run_code":                lambda a: "Đang thực thi code...",
    },
    "en": {
        "pdf_read_pages":          lambda a: f"Reading pages {a.get('page_start')}-{a.get('page_end')}...",
        "pdf_summarize_pages":     lambda a: f"Summarizing pages {a.get('page_start')}-{a.get('page_end')}...",
        "pdf_ocr_page":            lambda a: f"OCR page {a.get('page_number')}...",
        "pdf_ocr_page_detailed":   lambda a: f"Detailed OCR page {a.get('page_number')}...",
        "pdf_rag_search":          lambda a: "Searching semantically...",
        "pdf_extract_images":      lambda a: "Extracting images...",
        "pdf_read_pages_detailed": lambda a: f"Reading detailed pages {a.get('page_start')}-{a.get('page_end')}...",
        "run_code":                lambda a: "Executing code...",
    },
}


class _ActivityHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue, lang: str = "vi"):
        self._q = queue
        self._lang = lang
        self._response_maker_run_id = None
        self._streaming_llm_run_id = None

    async def on_chain_start(self, serialized, inputs, *, run_id, metadata=None, **kwargs):
        node = (metadata or {}).get("langgraph_node")
        if node == "response_maker":
            self._response_maker_run_id = run_id
        node_labels = NODE_LABELS.get(self._lang, NODE_LABELS["vi"])
        if node and node in node_labels:
            await self._q.put({"type": "activity", "text": node_labels[node]})

    async def on_tool_start(self, serialized, input_str, *, inputs=None, **kwargs):
        name = (serialized or {}).get("name", "")
        tool_labels = TOOL_LABELS.get(self._lang, TOOL_LABELS["vi"])
        if name not in tool_labels:
            return
        args = inputs or {}
        if not args and isinstance(input_str, str):
            try:
                args = json.loads(input_str)
            except Exception:
                args = {}
        await self._q.put({"type": "activity", "text": tool_labels[name](args)})

    async def on_llm_start(self, serialized, messages, *, run_id, parent_run_id=None, **kwargs):
        if parent_run_id == self._response_maker_run_id:
            self._streaming_llm_run_id = run_id

    async def on_llm_new_token(self, token: str, *, run_id, **kwargs):
        if run_id == self._streaming_llm_run_id and token:
            await self._q.put({"type": "token", "text": token})


_MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".xlsx", ".xls", ".csv", ".docx", ".md"}
    if ext not in allowed:
        raise HTTPException(400, f"Không hỗ trợ định dạng {ext}. Chỉ hỗ trợ: {', '.join(allowed)}")

    file_id = uuid.uuid4().hex
    dest = UPLOADS_DIR / f"{file_id}{ext}"

    size = 0
    try:
        with dest.open("wb") as f:
            while chunk := await file.read(1024 * 1024):  # đọc từng 1 MB
                size += len(chunk)
                if size > _MAX_UPLOAD_BYTES:
                    dest.unlink(missing_ok=True)
                    raise HTTPException(413, "File quá lớn. Giới hạn tối đa 100 MB.")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(500, f"Lỗi khi lưu file: {e}")

    return {"file_id": file_id, "filename": file.filename, "saved_as": dest.name}


@router.websocket("/chat/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        req_data = await websocket.receive_json()
    except Exception:
        await websocket.close(code=1003)
        return

    file_ids: list = req_data.get("file_ids", [])
    file_names_req: list = req_data.get("file_names", [])
    message: str = req_data.get("message", "")
    session_id: str = req_data.get("session_id", "default")
    lang: str = req_data.get("lang", "vi") if req_data.get("lang") in ("vi", "en") else "vi"

    is_safe, _ = await _check_injection(message)
    if not is_safe:
        await websocket.send_json({"type": "error", "text": _BLOCKED_MSG[lang]})
        await websocket.close()
        return

    file_paths = []
    _file_err = "File '{}' not found" if lang == "en" else "Không tìm thấy file '{}'"
    for fid in file_ids:
        matches = list(UPLOADS_DIR.glob(f"{fid}.*"))
        if not matches:
            await websocket.send_json({"type": "error", "text": _file_err.format(fid)})
            await websocket.close()
            return
        file_paths.append(str(matches[0]))

    config = {"configurable": {"thread_id": session_id}}
    file_names = file_names_req or [Path(p).name for p in file_paths]

    input_state = {
        "messages": [HumanMessage(content=message)],
        "file_path": file_paths[0] if file_paths else "",
        "file_paths": file_paths,
        "file_names": file_names,
        "summary": "",
        "analysis": {},
        "report_path": "",
        "slide_path": "",
        "lang": lang,
        "error": "",
    }

    queue: asyncio.Queue = asyncio.Queue()
    final_result: dict = {}

    async def run_graph():
        try:
            result = await graph_app.ainvoke(
                input_state,
                config={**config, "callbacks": [_ActivityHandler(queue, lang)]},
            )
            final_result.update(result)
        except Exception as e:
            final_result["error"] = str(e)
        finally:
            await queue.put(None)

    graph_task = asyncio.create_task(run_graph())

    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            await websocket.send_json(item)

        if final_result.get("error"):
            await websocket.send_json({"type": "error", "text": final_result["error"]})
            return

        output_files = []
        if final_result.get("report_path"):
            rp = Path(final_result["report_path"])
            if rp.exists():
                rel = rp.relative_to(UPLOADS_DIR)
                output_files.append({"id": str(rel).replace("\\", "/"), "name": rp.name, "type": "report"})
        if final_result.get("slide_path"):
            sp = Path(final_result["slide_path"])
            if sp.exists():
                rel = sp.relative_to(UPLOADS_DIR)
                output_files.append({"id": str(rel).replace("\\", "/"), "name": sp.name, "type": "slide"})
        for cp in final_result.get("chart_paths") or []:
            p = Path(cp)
            if p.exists():
                rel = p.relative_to(UPLOADS_DIR)
                output_files.append({"id": str(rel).replace("\\", "/"), "name": p.name, "type": "chart"})

        reply = final_result.get("summary") or final_result.get("analysis", {}).get("prose_summary", "")
        if reply:
            await graph_app.aupdate_state(config, {"messages": [AIMessage(content=reply)]})

        await websocket.send_json({"type": "done", "output_files": output_files, "content": reply})

    except WebSocketDisconnect:
        graph_task.cancel()
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    config = {"configurable": {"thread_id": session_id}}

    state = await graph_app.aget_state(config)
    if not state or not state.values:
        return {"messages": []}

    messages = []
    for msg in state.values.get("messages", []):
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})

    return {"messages": messages}


@router.get("/download/{filename:path}")
async def download_file(filename: str):
    file_path = (UPLOADS_DIR / filename).resolve()
    if not file_path.is_relative_to(UPLOADS_DIR.resolve()):
        raise HTTPException(403, "Forbidden.")
    if not file_path.exists():
        raise HTTPException(404, "File không tồn tại.")
    suffix = Path(filename).suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".pdf": "application/pdf",
                   ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
    media_type = media_types.get(suffix, "application/octet-stream")
    return FileResponse(path=str(file_path), filename=Path(filename).name, media_type=media_type)
