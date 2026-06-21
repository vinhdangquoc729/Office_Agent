import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel

from graph.graph import graph_app

router = APIRouter()

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


class ChatRequest(BaseModel):
    file_id: str
    message: str
    session_id: str = "default"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".xlsx", ".xls", ".docx", ".md"}
    if ext not in allowed:
        raise HTTPException(400, f"Không hỗ trợ định dạng {ext}. Chỉ hỗ trợ: {', '.join(allowed)}")

    file_id = uuid.uuid4().hex
    dest = UPLOADS_DIR / f"{file_id}{ext}"
    dest.write_bytes(await file.read())

    return {"file_id": file_id, "filename": file.filename, "saved_as": dest.name}


@router.post("/chat")
async def chat(req: ChatRequest):
    matches = list(UPLOADS_DIR.glob(f"{req.file_id}.*"))
    if not matches:
        raise HTTPException(404, "Không tìm thấy file. Vui lòng upload lại.")

    file_path = str(matches[0])
    thread_id = f"{req.session_id}_{req.file_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Chỉ truyền message mới + file_path; file_content/file_type được persist từ checkpointer
    input_state = {
        "messages": [HumanMessage(content=req.message)],
        "file_path": file_path,
        "summary": "",
        "analysis": {},
        "report_path": "",
        "slide_path": "",
        "error": "",
    }

    result = await graph_app.ainvoke(input_state, config=config)

    output_files = []
    if result.get("report_path"):
        rp = Path(result["report_path"])
        if rp.exists():
            output_files.append({"id": rp.name, "name": rp.name, "type": "report"})
    if result.get("slide_path"):
        sp = Path(result["slide_path"])
        if sp.exists():
            output_files.append({"id": sp.name, "name": sp.name, "type": "slide"})

    reply = result.get("summary") or result.get("analysis", {}).get("prose_summary", "Xử lý hoàn tất.")

    # Lưu AI reply vào message history để các turn sau có context
    await graph_app.aupdate_state(config, {"messages": [AIMessage(content=reply)]})

    return {
        "reply": reply,
        "output_files": output_files,
        "error": result.get("error", ""),
    }


@router.get("/history/{session_id}/{file_id}")
async def get_history(session_id: str, file_id: str):
    thread_id = f"{session_id}_{file_id}"
    config = {"configurable": {"thread_id": thread_id}}

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


@router.get("/download/{filename}")
async def download_file(filename: str):
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File không tồn tại.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )
