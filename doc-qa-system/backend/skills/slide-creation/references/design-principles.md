# Nguyên tắc thiết kế slide

Hướng dẫn toàn diện về typography, màu sắc, bố cục và trực quan hóa dữ liệu cho PPTX chuyên nghiệp.

---

## Typography

### Phân cấp kích thước

| Thành phần | Cỡ chữ | Độ đậm | Vai trò |
|---|---|---|---|
| Tiêu đề slide | 36-44pt | Bold/Black | Thu hút chú ý ngay lập tức |
| Phụ đề | 24-28pt | Medium | Ngữ cảnh bổ trợ |
| Nội dung | 18-24pt | Regular | Luận điểm chính |
| Caption | 14-16pt | Light | Chú thích, nguồn dữ liệu |

Cỡ chữ tối thiểu 14pt — không bao giờ nhỏ hơn để khán giả đọc được từ xa.

### Quy tắc ghép font

- Ghép 1 font tiêu đề đặc trưng với 1 font nội dung trung tính
- Sans-serif + sans-serif: hiện đại, sạch
- Serif + sans-serif: biên tập, tinh tế
- Monospace + sans-serif: kỹ thuật, developer
- Không dùng quá 2 font trong 1 bộ deck
- Font tiêu đề phải có weight Bold/Black

### Căn chỉnh và khoảng cách

- Căn trái cho nội dung (không căn đều cả 2 lề)
- Căn giữa chỉ cho tiêu đề, trích dẫn, số liệu lớn
- Khoảng dòng: 1.3-1.6x cỡ chữ
- Khoảng đoạn: 0.5-1x cỡ chữ

---

## Màu sắc

### Tương phản tối thiểu

- Chữ thường: tỷ lệ tương phản ≥ 4.5:1
- Chữ lớn (>24pt): tỷ lệ tương phản ≥ 3:1
- Kiểm tra tương phản trước khi dùng bất kỳ tổ hợp màu nào

### Quy tắc 60-30-10

- 60% màu nền chính
- 30% màu nền phụ và text phụ
- 10% màu nhấn (accent) — dùng cho điểm quan trọng, không trang trí

### Dùng màu nhất quán

- Màu nhấn = cùng một ý nghĩa xuyên suốt bộ deck
- Không thay đổi vai trò màu giữa các slide
- Nền tối: chữ sáng tối thiểu `#e0e0e0` (không dùng trắng thuần `#ffffff`)
- Nền sáng: chữ tối tối thiểu `#333333` (không dùng đen thuần `#000000`)

### Palette an toàn cho người mù màu

**Wong (8 màu):** `#000000, #E69F00, #56B4E9, #009E73, #F0E442, #0072B2, #D55E00, #CC79A7`

Dùng khi bộ deck có biểu đồ hoặc màu mang ý nghĩa (phân loại, so sánh).

---

## Bố cục

### Khoảng trắng

- Mục tiêu 40-50% diện tích mỗi slide là khoảng trống
- Khoảng trắng nhiều hơn = trông chuyên nghiệp hơn
- Không nhồi nội dung vào mọi góc slide
- Lề cố định tối thiểu 0.5 inch (≈ 1.3cm) từ mép

### Phân cấp thị giác

1. **Kích thước** — phần tử lớn hơn thu hút mắt trước
2. **Tương phản** — tương phản cao nổi bật hơn
3. **Vị trí** — trên trái và trung tâm được nhìn đầu tiên
4. **Cô lập** — phần tử có khoảng trống xung quanh có vẻ quan trọng
5. **Màu sắc** — màu sáng/bão hòa trên nền trung tính nổi bật nhất

### Kiểu bố cục phổ biến

| Kiểu | Dùng cho |
|---|---|
| Trung tâm | Slide tiêu đề, trích dẫn, chỉ số lớn |
| Chia đôi | So sánh, ảnh + văn bản |
| Chia lệch 60/40 | Nội dung chính + hình minh họa |
| Lưới 2x2 hoặc 3x2 | Tính năng, sản phẩm, nhóm người |

---

## Trực quan hóa dữ liệu

### Chọn loại biểu đồ

| Loại dữ liệu | Biểu đồ tốt nhất | Tránh |
|---|---|---|
| So sánh | Cột (bar) | Tròn (>5 phần) |
| Xu hướng theo thời gian | Đường (line) | Cột (>10 kỳ) |
| Tỷ lệ thành phần | Cột xếp chồng | Tròn (>5 phần) |
| Phân phối | Histogram | Đường |
| Tương quan | Điểm (scatter) | Cột |

### Đơn giản hóa biểu đồ cho slide

1. Bỏ hoặc làm mờ đường lưới
2. Gán nhãn trực tiếp lên dữ liệu, không dùng legend nếu tránh được
3. Giới hạn 3-4 chuỗi dữ liệu tối đa
4. Tô sáng insight chính bằng màu nhấn hoặc annotation
5. Dùng cỡ chữ lớn nhất có thể cho nhãn trục

### Trình bày dữ liệu phức tạp dần

1. **Slide tổng quan** — biểu đồ tổng thể + kết luận chính
2. **Slide chi tiết** — phóng to vùng quan trọng hoặc dữ liệu bổ trợ
3. **Slide diễn giải** — giải thích ý nghĩa và hàm ý

---

## Checklist trước khi hoàn thiện

- [ ] Font nhất quán xuyên suốt tất cả slide
- [ ] Màu nhấn mang cùng ý nghĩa ở mọi slide
- [ ] Tất cả chữ tối thiểu 14pt
- [ ] Tương phản đủ mạnh trên mọi nền
- [ ] Khoảng trắng rộng rãi và đồng đều
- [ ] Hình ảnh độ phân giải cao, không bị vỡ pixcel
- [ ] Không có từ lẻ hoặc ngắt dòng lạ ở tiêu đề
- [ ] Số slide hoặc thanh tiến trình hiển thị
- [ ] Kiểm tra ở độ phân giải 1920x1080

---

## Anti-patterns cần tránh

- **Font soup** — hơn 2 font trong 1 deck. Chọn 1 tiêu đề + 1 nội dung.
- **Color rainbow** — hơn 3 màu. Áp dụng quy tắc 60-30-10.
- **Wall of text** — chưng cất thành từ khóa và cụm từ.
- **Clip art syndrome** — mỗi hình ảnh phải có vai trò rõ ràng, không trang trí vô nghĩa.
- **AI slop aesthetics** — gradient tím, Inter/Roboto khắp nơi, card layout chung chung. Mỗi deck cần nhận diện thị giác riêng.
- **Cramming** — font không bao giờ nhỏ hơn 14pt. Nếu hết chỗ, tách slide.
