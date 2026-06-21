---
name: excel-analysis
description: Hướng dẫn phân tích file Excel nhiều sheet, xử lý header phức tạp và dữ liệu số
---

## Xử lý Excel nhiều sheet
- Parse TẤT CẢ sheets, ghi chú tên từng sheet trong output.
- Nếu có sheet tên "Summary" hoặc "Tổng hợp", đọc trước để nắm cấu trúc tổng thể.
- Ghi rõ sheet nào chứa dữ liệu thô, sheet nào chứa pivot/summary.

## Header bị merge
- Nếu row đầu tiên có merged cells, flatten về dòng đơn.
- Tên cột sau flatten: ghép các phần bằng dấu " > " (ví dụ: "Doanh thu > Q1").

## Định dạng ngày tháng
- Tự động nhận diện cột ngày (date), convert sang ISO 8601 (YYYY-MM-DD).
- Cảnh báo nếu có mixed format trong cùng một cột.

## Giá trị bất thường cần kiểm tra
- Giá trị âm trong cột tiền/doanh thu/số lượng → ghi chú là anomaly.
- Giá trị null hoặc 0 chiếm > 20% một cột → cảnh báo chất lượng dữ liệu.
- Giá trị outlier (> 3 lần độ lệch chuẩn) → đánh dấu để xác minh.

## Phân tích xu hướng
- Nếu có dữ liệu theo thời gian, tính tăng trưởng kỳ-so-kỳ (QoQ, MoM, YoY).
- So sánh thực tế vs kế hoạch nếu có cả hai cột.
