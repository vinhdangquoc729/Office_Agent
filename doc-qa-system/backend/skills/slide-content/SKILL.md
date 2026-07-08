---
name: slide-content
description: Hướng dẫn analyst soạn nội dung chi tiết cho bài thuyết trình khi được yêu cầu tạo slide
---

## Nhiệm vụ và quy trình

Khi skill này được kích hoạt, analyst đọc tài liệu và soạn slide_outline theo quy trình sau:

Gọi `pdf_summarize_pages` từng batch 5-7 trang. Sau **mỗi batch**, ngay lập tức xử lý những trang đáng chú ý thay vì chờ summarize hết:
- Trang có nội dung quan trọng cho bài thuyết trình → gọi `pdf_read_pages` để đọc chi tiết
- Trang có `images[]` không rỗng với ảnh kích thước > 50pt → gọi `pdf_extract_images` rồi `pdf_annotate_images` ngay

Sau khi đã đọc/extract đủ, xây dựng `slide_outline` JSON với path tuyệt đối từ manifest điền vào `images[]`. Trả về ONLY JSON — không có prose text, không có code block wrapper.

Analyst chịu trách nhiệm về nội dung. Slide creator chịu trách nhiệm về hình thức và bố cục.

## Output: trường "slide_outline" trong analysis

Điền trường `slide_outline` với cấu trúc sau:

```json
{
  "slide_outline": {
    "theme": "cleanCorporate",
    "presentation_title": "Tiêu đề bài thuyết trình",
    "estimated_duration": "15 min",
    "sections": [
      {
        "heading": "Tiêu đề phần",
        "type_hint": "content",
        "narrative": "Nội dung đầy đủ sẽ trình bày trong phần này...",
        "metrics": [],
        "images": []
      }
    ]
  }
}
```

## Chọn theme

| Theme | Phù hợp với |
|---|---|
| cleanCorporate | Báo cáo doanh nghiệp, trình bày chính thức (mặc định) |
| darkMonospace | Tài liệu kỹ thuật, tech, AI/ML |
| swissModern | Marketing, thiết kế, sáng tạo |
| boldSignal | Startup, pitch deck |
| warmMinimal | Giáo dục, khóa học, đào tạo |

## Quy mô outline theo thời lượng

| Thời lượng | Số section dự kiến | Cấu trúc khuyến nghị |
|---|---|---|
| 5 phút | 4-5 | Hook, 2-3 điểm chính, Kết |
| 15 phút | 7-10 | Mở đầu, 3-4 chương, Tóm tắt, Kết |
| 30 phút | 12-18 | Title, Agenda, 5-6 chương, Q&A |
| 45+ phút | 18-25 | Title, Agenda, 7-8 chương, Summary, Q&A |

Nếu người dùng không nêu thời lượng, mặc định 15 phút.

## Loại slide (type_hint)

| type_hint | Dùng khi |
|---|---|
| title | Slide bìa, mở đầu toàn bài |
| agenda | Danh sách mục lớn của bài |
| section-divider | Chuyển sang chương/phần mới |
| content | Trình bày luận điểm, phân tích, giải thích |
| metrics | 2-4 con số quan trọng cần nổi bật |
| comparison | So sánh 2 phương án, giai đoạn, đối tượng |
| timeline | Chuỗi sự kiện hoặc mốc thời gian |
| feature-grid | 3-6 tính năng, đặc điểm, điểm mạnh |
| quote | Trích dẫn đáng chú ý |
| image-focus | Phần chủ yếu dựa vào hình ảnh |
| closing | Kết luận, đề xuất hành động, Q&A |

## Yêu cầu về narrative

Mỗi section PHẢI có `narrative` đủ chi tiết để người không đọc tài liệu gốc vẫn nắm được nội dung:

- Viết đầy đủ câu — không viết tắt hay liệt kê keywords
- Đưa số liệu cụ thể, không dùng "cao", "nhiều", "đáng kể"
- Giải thích ngữ cảnh và ý nghĩa, không chỉ nêu facts
- Nêu rõ kết luận hoặc thông điệp chính của phần đó
- Dài ít nhất 4-6 câu, không có giới hạn trên

Ví dụ ĐÚNG:
```
"Tổng số sinh viên xuất hiện trong cả 2 kỳ là 229 người, chiếm 45% tổng sinh viên
toàn khóa. Đây là nhóm có tính ổn định cao — tỷ lệ chuyển lớp chỉ 8%, thấp hơn
mức trung bình khoa 15%. Phòng học được sử dụng nhiều nhất là 308A với 12 buổi/tuần,
tiếp theo là 204B (9 buổi) và 105C (7 buổi). Sự tập trung vào 308A đặt ra câu hỏi
về phân bổ phòng học cho kỳ tới."
```

Ví dụ SAI:
```
"229 sinh viên chung, phòng 308A đông nhất"
```

## Trường metrics và images

**metrics**: mảng string mô tả chỉ số quan trọng — ghi rõ giá trị và ngữ cảnh:
```json
"metrics": ["229 sinh viên / 2 kỳ", "+340% doanh thu Q4 so Q3", "308A: 12 buổi/tuần"]
```

**images**: đường dẫn tuyệt đối từ pdf_extract_images — chỉ điền nếu đã extract được ảnh thực, không đặt đường dẫn giả.

## Khi nào và cách trích xuất ảnh

Sau khi `pdf_summarize_pages` xong, **phải** gọi `pdf_extract_images` cho những trang mà summary của trang đó gợi ý có hình ảnh nội dung quan trọng:
- Trang bị ghi là "contains only images" hoặc "no extractable text" nhưng có `images[]` không rỗng → đây thường là sơ đồ hoặc hình full-page
- Trang chứa biểu đồ, sơ đồ kiến trúc, infographic liên quan đến nội dung thuyết trình
- Section có `type_hint: "image-focus"` hoặc `metrics` và trang tương ứng có ảnh

**Không cần extract:** trang chỉ có ảnh nhỏ (logo, icon, header trang trí) hoặc tài liệu không phải PDF.

**Quy trình:**

1. Gọi `pdf_extract_images(file_index, page_start, page_end)` cho trang đã xác định ở trên
2. Từ manifest trả về, bỏ qua ảnh nhỏ hơn 50pt hoặc là logo/watermark
3. Gọi `pdf_annotate_images(file_index, annotations)` để ghi mô tả cho từng ảnh đã chọn
4. Điền path tuyệt đối vào `images[]` của section tương ứng

Dùng đúng giá trị trường `path` từ manifest trả về bởi `pdf_extract_images`. KHÔNG được đặt đường dẫn tự đặt hay ví dụ giả.
