# Doc-QA System

Chatbot phân tích tài liệu nội bộ — upload file, đặt yêu cầu bằng tiếng Việt, nhận phân tích / báo cáo / slide.

## Tính năng

- Upload PDF, XLSX, DOCX, Markdown
- Phân tích dữ liệu, tóm tắt, trả lời câu hỏi
- Tạo báo cáo `.docx`
- Tạo slide `.pptx` với ảnh từ PDF (tự động layout theo hướng ảnh)
- Multi-agent pipeline: Supervisor → Document Loader → Analyst → Reporter / Slide Creator
- Skill system: mỗi agent load thêm hướng dẫn nghiệp vụ tuỳ yêu cầu (Progressive Disclosure)

## Kiến trúc

```
doc-qa-system/
├── backend/
│   ├── main.py
│   ├── api/routes.py          # POST /chat, POST /upload, GET /download/{id}
│   ├── graph/                 # LangGraph StateGraph
│   │   ├── state.py
│   │   ├── graph.py
│   │   └── router.py
│   ├── agents/                # Các agent node
│   │   ├── supervisor.py
│   │   ├── document_loader.py
│   │   ├── analyst.py         # ReAct loop, MAX_ITERATIONS=15
│   │   ├── summarizer.py
│   │   ├── reporter.py
│   │   ├── slide_creator.py
│   │   └── helpers/
│   ├── prompts/               # System prompt của từng agent (*.md)
│   ├── skills/                # SKILL.md — hướng dẫn nghiệp vụ
│   │   ├── excel-analysis/
│   │   ├── pdf-extraction/
│   │   ├── report-writing/
│   │   ├── slide-content/     # Dành cho analyst khi tạo slide
│   │   └── slide-creation/    # Dành cho slide_creator (formatter)
│   ├── tools/
│   │   ├── file_readers.py
│   │   ├── analysis.py
│   │   ├── output_writers.py  # create_pptx, write_report_docx
│   │   ├── image_extractor.py
│   │   └── rag_store.py
│   └── uploads/               # File upload + output (git-ignored)
└── frontend/
    └── src/
        └── components/        # ChatWindow, MessageBubble, FileUpload
```

## Cài đặt

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Tạo file `.env`:

```
OPENAI_API_KEY=sk-...
```

Chạy server:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## API

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/upload` | Upload file → `{file_id, filename}` |
| POST | `/chat` | Gửi tin nhắn → `{reply, output_files[]}` |
| GET | `/download/{file_id}` | Tải file output |

## Stack

| Layer | Công nghệ |
|-------|-----------|
| LLM | OpenAI GPT-4o |
| Orchestration | LangGraph |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite |
| PDF | pdfplumber + PIL |
| Output | python-pptx + python-docx |
| RAG | LangChain in-memory vector store |
