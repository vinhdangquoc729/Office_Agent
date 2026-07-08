# Doc-QA System

Chatbot phân tích tài liệu nội bộ — upload file, đặt yêu cầu bằng tiếng Việt hoặc tiếng Anh, nhận phân tích / tóm tắt / báo cáo / slide trực tiếp trong trình duyệt.

---

## Tính năng

### Xử lý tài liệu
- Upload nhiều file cùng lúc: **PDF, XLSX, DOCX, Markdown** (tối đa 100 MB/file)
- Đọc nội dung, OCR ảnh trong PDF, tìm kiếm ngữ nghĩa (RAG)
- Trả lời câu hỏi cụ thể, tóm tắt theo yêu cầu

### Output tự động
- Tạo báo cáo **`.docx`** với nội dung cấu trúc đầy đủ
- Tạo slide **`.pptx`** qua TypeScript (PptxGenJS) — layout tự động theo hướng ảnh
- Xuất biểu đồ (chart) khi cần phân tích dữ liệu Excel

### Kiến trúc agent
- **Multi-agent**: Supervisor → Document Loader → Analyst → Reporter / Slide Creator / Summarizer / Response Maker
- **Single-agent**: Supervisor → Document Loader → Universal Agent (tất cả trong một)
- Chuyển đổi giữa 2 chế độ ngay trong giao diện cài đặt

### Giao diện
- Streaming token từng chữ — không chờ đợi im lặng
- Hiển thị activity realtime: "Đang đọc trang X-Y...", "Đang OCR trang N..."
- Hỗ trợ **Tiếng Việt / English** — prompt agent thay đổi theo ngôn ngữ
- Chủ đề **Sáng / Tối**
- Lưu lịch sử hội thoại qua localStorage

### Bảo mật
- Input guard (GPT-4o-mini) chặn prompt injection trước khi xử lý

### Benchmark
- Runner tự động gửi test case qua WebSocket, đo latency + token + cost
- LLM-as-judge chấm điểm 4 chiều: task completion, accuracy, format, conciseness
- Kết quả merge (không ghi đè) khi chạy lại từng case

---

## Kiến trúc

```
doc-qa-system/
├── backend/
│   ├── main.py                    # FastAPI app, mount 2 graph (multi + single)
│   ├── api/
│   │   └── routes.py              # WebSocket /chat/ws, POST /upload, GET /download
│   ├── graph/
│   │   ├── state.py               # DocQAState TypedDict
│   │   ├── graph.py               # Multi-agent StateGraph
│   │   ├── graph_single.py        # Single-agent StateGraph
│   │   └── router.py              # Conditional edge logic
│   ├── agents/
│   │   ├── supervisor.py          # Phân loại yêu cầu (qa / summarize / report / slide)
│   │   ├── chat.py                # Hội thoại thông thường (không có file)
│   │   ├── document_loader.py     # Đọc và index tài liệu
│   │   ├── analyst.py             # ReAct loop (MAX_ITERATIONS=15), gọi PDF/Excel tools
│   │   ├── universal_agent.py     # Single-agent thay thế analyst + tất cả output agents
│   │   ├── summarizer.py          # Tóm tắt từ kết quả analyst
│   │   ├── reporter.py            # Tạo báo cáo .docx
│   │   ├── slide_creator.py       # Tạo slide .pptx qua TypeScript
│   │   ├── response_maker.py      # Soạn câu trả lời cuối (streaming)
│   │   └── helpers/pdf_helper.py  # Tool đọc PDF dùng chung
│   ├── prompts/                   # System prompt của từng agent
│   │   ├── supervisor.md + .en.md
│   │   ├── analyst.md + .en.md
│   │   └── ...                    # 10 agent × 2 ngôn ngữ
│   ├── skills/                    # SKILL.md — hướng dẫn nghiệp vụ
│   │   ├── excel-analysis/        # SKILL.md + .en.md
│   │   ├── data-qa/               # SKILL.md + .en.md
│   │   ├── report-writing/        # SKILL.md + .en.md
│   │   └── pptx-slides/           # TypeScript source (PptxGenJS)
│   ├── tools/
│   │   ├── file_readers.py        # PDF, Excel, DOCX, Markdown parser
│   │   ├── output_writers.py      # write_report_docx, run_ts_script
│   │   ├── image_extractor.py     # Trích xuất ảnh từ PDF
│   │   └── rag_store.py           # In-memory vector store (LangChain)
│   └── uploads/                   # File upload + output (git-ignored)
├── frontend/
│   └── src/
│       ├── App.tsx                # Layout, conversation state
│       ├── i18n.ts                # Context: lang, theme, agentMode
│       ├── api/client.ts          # WebSocket sendMessageStream
│       └── components/
│           ├── ChatWindow.tsx     # Stream loop, message state
│           ├── MessageBubble.tsx  # Render markdown, activity, download
│           ├── Sidebar.tsx        # Danh sách hội thoại + Settings panel
│           ├── FileUpload.tsx     # Drag & drop, multi-file
│           └── DownloadButton.tsx
└── benchmark/
    ├── test_cases.json            # 10 test case (qa, summarize, analyze, report, slide)
    ├── runner.py                  # Chạy benchmark, ghi results.json
    ├── judge.py                   # LLM-as-judge, ghi scores.json
    ├── results.json               # Kết quả latency/token/cost/output
    └── scores.json                # Điểm 4 chiều per case per mode
```

---

## Luồng xử lý (Multi-agent)

```
User message
    │
    ▼
[Supervisor] — phân loại intent
    │
    ├─ chat ──────────────────────────────► [Chat] ──► END
    │
    └─ document task ─► [Document Loader]
                              │
                              ▼
                         [Analyst]  ◄── ReAct loop (PDF tools, RAG, code exec)
                              │
                    ┌─────────┼──────────┬──────────┐
                    ▼         ▼          ▼          ▼
               [Summarizer] [Reporter] [Slide]  [Response Maker]
                    │         │          │          │
                    └─────────┴──────────┴──────────┘
                                    │
                                   END  (streaming done event)
```

---

## Cài đặt

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# hoặc: source .venv/bin/activate  (Linux/Mac)
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

Trong môi trường dev, Vite proxy tự động chuyển `/upload`, `/chat/ws`, `/download` sang `localhost:8000`.

---

## API

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/upload` | Upload file → `{file_id, filename}` |
| WS | `/chat/ws` | WebSocket streaming — nhận `activity`, `token`, `done`, `error` events |
| GET | `/download/{path}` | Tải file output (docx, pptx, png) |
| GET | `/history/{session_id}` | Lịch sử hội thoại |

### WebSocket payload (client → server)

```json
{
  "file_ids": ["abc123"],
  "file_names": ["bao_cao.pdf"],
  "message": "Tóm tắt báo cáo trong 5 điểm chính",
  "session_id": "conv_xyz",
  "lang": "vi",
  "mode": "multi"
}
```

### WebSocket events (server → client)

```json
{ "type": "activity", "text": "Đang đọc trang 1-5..." }
{ "type": "token",    "text": "Kỹ thuật" }
{ "type": "done",     "content": "...", "output_files": [...],
  "input_tokens": 12000, "output_tokens": 800, "cost_usd": 0.038 }
{ "type": "error",    "text": "..." }
```

---

## Benchmark

```bash
cd backend

# Upload file trước, lấy file_id
curl -X POST http://localhost:8000/upload -F "file=@../benchmark/sample.pdf"

# Chạy toàn bộ 10 case × 2 mode
python ../benchmark/runner.py --pdf-id <file_id>

# Chạy lại 1 case cụ thể (merge, không ghi đè)
python ../benchmark/runner.py --pdf-id <file_id> --id pdf_summarize --mode single

# Chấm điểm bằng LLM judge
python ../benchmark/judge.py
```

Kết quả tổng hợp (10 cases, GPT-4o):

| Mode | Avg Score | Total Cost | Ghi chú |
|---|:---:|---:|---|
| Multi-agent | 3.78 / 5 | ~$2.46 | Mạnh ở QA + VN30 table; yếu ở summarize (dùng image thay text) |
| Single-agent | 4.03 / 5 | ~$0.60 | Tốt hơn QA; lỗi slide (TS syntax); cost thấp hơn 4× |

---

## Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Orchestration | LangGraph (StateGraph + checkpointing) |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + TypeScript |
| PDF | pdfplumber + PIL |
| Excel | pandas + openpyxl |
| Output | python-pptx, python-docx |
| Slide codegen | PptxGenJS (TypeScript, bundled với esbuild) |
| RAG | LangChain in-memory vector store |
| Token tracking | Custom `AsyncCallbackHandler` (langchain-core) |
