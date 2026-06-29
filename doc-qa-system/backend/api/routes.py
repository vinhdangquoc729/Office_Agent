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
    file_ids: list[str]
    file_names: list[str] = []
    message: str
    session_id: str = "default"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".xlsx", ".xls", ".csv", ".docx", ".md"}
    if ext not in allowed:
        raise HTTPException(400, f"Không hỗ trợ định dạng {ext}. Chỉ hỗ trợ: {', '.join(allowed)}")

    file_id = uuid.uuid4().hex
    dest = UPLOADS_DIR / f"{file_id}{ext}"
    dest.write_bytes(await file.read())

    return {"file_id": file_id, "filename": file.filename, "saved_as": dest.name}


@router.post("/chat")
async def chat(req: ChatRequest):
    file_paths = []
    for fid in req.file_ids:
        matches = list(UPLOADS_DIR.glob(f"{fid}.*"))
        if not matches:
            raise HTTPException(404, f"Không tìm thấy file '{fid}'. Vui lòng upload lại.")
        file_paths.append(str(matches[0]))

    thread_id = req.session_id
    config = {"configurable": {"thread_id": thread_id}}

    file_names = req.file_names or [Path(p).name for p in file_paths]

    input_state = {
        "messages": [HumanMessage(content=req.message)],
        "file_path": file_paths[0],
        "file_paths": file_paths,
        "file_names": file_names,
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
            rel = rp.relative_to(UPLOADS_DIR)
            output_files.append({"id": str(rel).replace("\\", "/"), "name": rp.name, "type": "report"})
    if result.get("slide_path"):
        sp = Path(result["slide_path"])
        if sp.exists():
            rel = sp.relative_to(UPLOADS_DIR)
            output_files.append({"id": str(rel).replace("\\", "/"), "name": sp.name, "type": "slide"})
    for cp in result.get("chart_paths") or []:
        p = Path(cp)
        if p.exists():
            rel = p.relative_to(UPLOADS_DIR)
            output_files.append({"id": str(rel).replace("\\", "/"), "name": p.name, "type": "chart"})

    reply = result.get("summary") or result.get("analysis", {}).get("prose_summary", "Xử lý hoàn tất.")

    await graph_app.aupdate_state(config, {"messages": [AIMessage(content=reply)]})

    return {
        "reply": reply,
        "output_files": output_files,
        "error": result.get("error", ""),
    }


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
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File không tồn tại.")
    suffix = Path(filename).suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".pdf": "application/pdf",
                   ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
    media_type = media_types.get(suffix, "application/octet-stream")
    return FileResponse(path=str(file_path), filename=Path(filename).name, media_type=media_type)
