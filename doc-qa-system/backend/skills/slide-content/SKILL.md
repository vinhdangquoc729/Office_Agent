---
name: slide-content
description: Hướng dẫn analyst chuẩn bị nội dung outline slide khi yêu cầu tạo slide thuyết trình
---

## Nhiệm vụ BẮT BUỘC

Khi skill này được kích hoạt, trường "slides" trong output JSON PHẢI được điền — đây là output chính của yêu cầu:
- Đọc kỹ tài liệu để có đủ thông tin cho từng slide
- Extract ảnh từ PDF nếu tài liệu có hình (ưu tiên extract các trang có hình ảnh nhúng)
- Build trường "slides" trước khi kết thúc — KHÔNG được trả output mà "slides" vẫn là []

## Trường "slides" trong output

"slides" là array các slide theo thứ tự. Mỗi phần tử tuân theo một trong 6 schema layout sau:

Layout cover — slide bìa, luôn là slide đầu tiên:
{"layout": "cover", "title": "Tiêu đề báo cáo", "subtitle": "Tác giả / Ngày / Học phần"}

Layout bullets — danh sách bullet, dùng phổ biến nhất:
Mỗi bullet CÓ THỂ là string đơn giản, hoặc object {"text": "...", "sub": "..."} nếu cần giải thích thêm.
{"layout": "bullets", "number": 1, "title": "Kết quả nổi bật năm 2024", "bullets": [
  {"text": "Q4 +340% so Q3", "sub": "Tăng trưởng cao nhất từ trước đến nay"},
  {"text": "Sản phẩm A chiếm 67% doanh thu", "sub": "Tăng từ 45% so cùng kỳ"},
  "Khu vực Miền Bắc dẫn đầu"
]}

Layout bullets_image1 — bullets + 1 ảnh (vị trí tự động theo chiều ảnh):
{"layout": "bullets_image1", "number": 2, "title": "Kiến trúc hệ thống", "bullets": ["Pipeline 3 bước xử lý", "Entity Linking tự động"], "images": ["/tuyệt đối/đường/dẫn/ảnh.png"], "captions": ["Hình 5: Sơ đồ kiến trúc pipeline NLP"]}

Layout bullets_image2 — bullets + 2 ảnh (vị trí tự động theo chiều ảnh):
{"layout": "bullets_image2", "number": 3, "title": "So sánh mô hình", "bullets": ["PhoBERT F1 = 0.724", "Baseline F1 = 0.61"], "images": ["/path/img1.png", "/path/img2.png"], "captions": ["Hình 8: Accuracy theo epoch", "Hình 9: Confusion matrix"]}

Layout images — 1 hoặc 2 ảnh, không có bullet:
{"layout": "images", "number": 4, "title": "Biểu đồ tương quan sentiment", "images": ["/path/chart.png"], "captions": ["Hình 12: Tương quan lag 0-5 ngày"]}

Layout image_text — ảnh + đoạn văn (vị trí tự động theo chiều ảnh):
{"layout": "image_text", "number": 5, "title": "Phân tích sự kiện", "images": ["/path/event.png"], "captions": ["Hình 15: Cumulative return sau sự kiện"], "text": "Giá cổ phiếu phản ứng mạnh trong vòng 1 ngày sau sự kiện lớn, biên độ trung bình ±3.2%."}

## Quy tắc viết bullet

- Từ 3-6 bullets mỗi slide content (trừ slide cover và slide Q&A cuối)
- Mỗi bullet text có từ 5-15 từ
- Bắt đầu bằng số liệu cụ thể hoặc từ hành động (không bắt đầu bằng "Các", "Về")
- Tiêu đề slide = kết luận hoặc thông điệp chính, không phải nhãn chủ đề

Sub-bullet (trường "sub"):
- Nên dùng cho slide KHÔNG có ảnh (layout "bullets") để giải thích thêm ý nghĩa bullet chính
- Mỗi sub tối đa 15 từ, ngắn gọn và cụ thể
- Slide có ảnh (bullets_image1, bullets_image2) KHÔNG dùng sub vì đã có ảnh minh hoạ

## Quy tắc dùng ảnh

- Chỉ dùng layout có ảnh nếu đã có đường dẫn ảnh thực từ pdf_extract_images
- Dùng trường "path" từ manifest — đường dẫn tuyệt đối đến file PNG
- Ưu tiên ảnh có trường "about" đã được annotate
- Không đặt đường dẫn giả vào images nếu chưa extract
- Vị trí ảnh (ngang/dọc, trên/dưới, trái/phải) được xử lý tự động bởi renderer
- Trường "captions": array string song song với "images" — caption cho từng ảnh theo thứ tự
- Caption lấy từ trường "about" trong manifest hoặc từ caption text gần ảnh trong PDF (ví dụ "Hình X: ...")
- Nếu không có caption, bỏ qua trường "captions" hoặc để []

## Luồng làm việc khi tạo slide từ PDF

Bước 1: Đọc nội dung tài liệu — dùng pdf_rag_search hoặc pdf_summarize_pages để nắm cấu trúc.
Bước 2: Đọc chi tiết các phần quan trọng — dùng pdf_read_pages cho các trang có dữ liệu, bảng biểu, kết quả.
Bước 3 (nếu tài liệu có hình): Gọi pdf_extract_images cho các trang có hình ảnh liên quan.
Bước 4 (nếu có ảnh): Gọi pdf_read_pages cho các trang đó, annotate bằng pdf_annotate_images.
Bước 5: Build outline "slides" dựa trên nội dung đã đọc.

## Cấu trúc deck chuẩn

- Slide 1: layout "cover" — tiêu đề + tác giả/ngày
- Slide 2: layout "bullets" — agenda (3-5 mục lớn sẽ trình bày)
- Slide 3 đến N-1: nội dung chính, mỗi key finding hoặc chủ đề lớn là 1 slide
- Slide N-1: layout "bullets" — kết luận + đề xuất hành động
- Slide N: layout "bullets", bullets=[] — "Câu hỏi & Thảo luận"

## Số slide theo độ dài báo cáo

Báo cáo ngắn (dưới 15 trang): 6-8 slide
Báo cáo trung bình (15-40 trang): 10-14 slide
Báo cáo dài (trên 40 trang): 14-20 slide
Nếu user yêu cầu "chi tiết" hoặc "đầy đủ": không giới hạn, mỗi chương/phần lớn có khoảng 1-3 slide
