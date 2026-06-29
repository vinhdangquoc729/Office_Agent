---
name: pdf-extraction
description: Hướng dẫn xử lý các loại PDF khác nhau, sử dụng các tool đọc PDF theo trang
---

## Các tool có thể dùng

Tất cả tool PDF đều nhận file_index (số nguyên, index trong danh sách tài liệu) thay vì file_path.
Danh sách tài liệu và index tương ứng có trong phần đầu ngữ cảnh.

pdf_get_page_count(file_index)
- Trả về: số nguyên là tổng số trang
- Dùng khi chưa biết độ dài tài liệu (file_content đã có total_pages từ metadata, dùng khi cần xác nhận)

pdf_summarize_pages(file_index, page_start, page_end)
- Nhờ helper tóm tắt nội dung từng trang trong khoảng [page_start, page_end] (1-indexed, inclusive)
- Mỗi trang trả về: page_number, summary, images (tọa độ)
- Gọi tối đa 5-7 trang mỗi lần — helper không đủ thông minh để xử lý nhiều hơn
- Dùng để: nắm sơ bộ nội dung trước khi quyết định đọc chi tiết

pdf_read_pages(file_index, page_start, page_end)
- Trả về: danh sách trang, mỗi trang gồm text, tables, images (vị trí + kích thước), annots
- Dùng khi: yêu cầu hỏi về nội dung cụ thể của trang đã biết
- Ưu tiên dùng cái này thay vì summarize khi cần dữ liệu chính xác (tên người, số liệu, bảng)

pdf_read_pages_detailed(file_index, page_start, page_end)
- Giống pdf_read_pages nhưng thêm chars (font, size, màu, tọa độ), lines, rects
- Chỉ dùng khi cần biết vị trí chính xác các phần tử (detect heading, phân tích layout)
- Nặng hơn — hạn chế dùng

pdf_extract_images(file_index, page_start, page_end)
- Trích xuất ảnh từ khoảng trang chỉ định, lưu ra disk, trả về manifest JSON
- Trang đã extract trước đó sẽ được bỏ qua (không làm lại)
- Manifest gồm: filename, path, page, index, x0/y0/x1/y1, width_pt/height_pt
- Dùng khi: cần đưa ảnh vào slide, hoặc người dùng hỏi về hình ảnh trong tài liệu

pdf_annotate_images(file_index, annotations)
- Ghi trường "about" (mô tả) cho từng ảnh trong manifest
- annotations: [{"filename": "page005_img01.png", "about": "Biểu đồ doanh thu Q1-Q4 2024"}]
- Gọi SAU khi đã đọc text trang đó để suy luận nội dung ảnh

pdf_ocr_page(file_index, page_number)
- OCR trang PDF, trả về text thuần đã ghép theo thứ tự từ trên xuống
- Dùng khi pdf_read_pages có _ocr_hint hoặc text sơ sài mà trang có ảnh
- Chậm hơn pdf_read_pages — chỉ dùng khi cần thiết

pdf_ocr_page_detailed(file_index, page_number)
- Giống pdf_ocr_page nhưng trả về list blocks đầy đủ: {text, confidence, x0, y0, x1, y1}
- Dùng khi cần biết vị trí chính xác của text (caption, layout, vùng cụ thể trong trang)

run_code(code)
- Chạy Python (pandas, numpy) để tính toán, thống kê
- Dùng khi cần xử lý dữ liệu đã đọc được

pdf_rag_search(file_index, query)
- Tìm kiếm ngữ nghĩa toàn bộ tài liệu, trả về các đoạn văn liên quan nhất kèm số trang
- Lần đầu gọi sẽ index toàn bộ (chậm hơn), các lần sau nhanh
- Dùng khi: tài liệu dài, không biết thông tin ở trang nào

## Chiến lược đọc tài liệu

Nếu yêu cầu hỏi về trang cụ thể (ví dụ "trang 69 gồm những ai"):
- Gọi thẳng pdf_read_pages với đúng trang đó
- Nếu trang có _ocr_hint hoặc text sơ sài trong khi images[] không rỗng → PHẢI gọi pdf_ocr_page để đọc nội dung trong ảnh
- Nếu text rỗng hoàn toàn → PHẢI gọi pdf_ocr_page
- Chỉ dùng pdf_ocr_page_detailed khi cần tọa độ chính xác (layout, vị trí caption)

Nếu cần tìm thông tin nhưng không biết trang nào (tài liệu > 30 trang):
- Dùng pdf_rag_search(file_index, query) để định vị trang
- Sau đó gọi pdf_read_pages cho các trang tìm được để đọc đầy đủ

Nếu tài liệu ngắn (< 30 trang) và cần phân tích toàn bộ:
- Dùng pdf_summarize_pages theo chunk 5-7 trang
- Chỉ đọc chi tiết các chunk có thông tin quan trọng

## Luồng xử lý ảnh

Khi cần hiểu hoặc sử dụng ảnh trong tài liệu:

Bước 1: Gọi pdf_extract_images để trích xuất ảnh từ các trang liên quan.
Bước 2: Gọi pdf_read_pages cho chính các trang đó để lấy text.
Bước 3: Với mỗi ảnh trong manifest, dùng thông tin vị trí (x0/y0/x1/y1) để xác định text nằm gần ảnh (caption, tiêu đề, chú thích). Text có y gần với y1 của ảnh thường là caption phía dưới.
Bước 4: Gọi pdf_annotate_images để ghi mô tả đã suy luận vào manifest.
Bước 5: Dùng "path" từ manifest để truyền vào slide layout.

## Phân biệt loại PDF

Text-based PDF: text extract chính xác, bảng và danh sách được nhận dạng.
Scanned PDF: text rỗng hoặc ít, không thể extract — cảnh báo người dùng.
Mixed: ghi chú từng trang nếu có trang scanned.

## Xử lý bảng bị vỡ qua nhiều trang

Ghép lại dựa trên header cột giống nhau. Nếu không thể ghép, trình bày từng phần và ghi chú "tiếp theo từ trang X".

## Xử lý hình ảnh

Khi images[] của trang không rỗng: ghi chú "[Hình ảnh tại trang X, vị trí (x0,y0)-(x1,y1)]".
Nếu hình có caption liền kề, trích dẫn caption.
