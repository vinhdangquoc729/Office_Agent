---
name: excel-analysis
description: Hướng dẫn phân tích file Excel nhiều sheet, xử lý header phức tạp và dữ liệu số
---

## Xử lý Excel nhiều sheet
- Parse TẤT CẢ sheets, ghi chú tên từng sheet trong output.
- Nếu có sheet tên "Summary" hoặc "Tổng hợp", đọc trước để nắm cấu trúc tổng thể.
- Ghi rõ sheet nào chứa dữ liệu thô, sheet nào chứa pivot/summary.

## Đọc file với header đúng
Các biến sau được inject tự động vào mỗi lần gọi run_code:
- file_path: đường dẫn file đầu tiên (= file_paths[0])
- file_paths: list đường dẫn tất cả file trong conversation
- files_metadata: list dict {suggested_header_row, sheets_columns} theo cùng index với file_paths
- suggested_header_row: header row của file_paths[0]
- sheet_names: list tên sheet của file_paths[0]
- sheets_columns: dict {sheet_name: [tên cột]} của file_paths[0]

Pattern chuẩn — 1 file:
  import pandas as pd
  df = pd.read_excel(file_path, sheet_name=sheet_names[0], header=suggested_header_row)
  print(df.columns.tolist())          # luôn in tên cột trước khi truy cập

Pattern — nhiều file (truy cập file thứ 2 trở đi):
  import pandas as pd
  # Đọc file_paths[1] với metadata đúng của nó
  meta1 = files_metadata[1]
  df1 = pd.read_excel(file_paths[1], header=meta1['suggested_header_row'])
  print(df1.columns.tolist())

Lưu ý cột số nguyên: nếu sheets_columns chứa 1, 6, 9 (số nguyên), truy cập bằng int:
  df[1]  # Đúng
  df['1']  # Sai — KeyError

Nếu tên cột sai sau khi dùng suggested_header_row:
1. Thử lần lượt header=0 đến header=9 (tối đa 10 lần), in df.columns mỗi lần.
2. Sau 10 lần vẫn không được, đọc raw (header=None, nrows=12) rồi in toàn bộ.

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

## Tạo biểu đồ

Biến `output_dir` đã được inject sẵn — lưu ảnh vào đó để frontend có thể download.

BUOC 1 — GỌI TOOL NÀY TRƯỚC KHI VIẾT BẤT KỲ CODE CHART NÀO:
  read_reference(skill="excel-analysis", filename="chart_templates.md")
Chọn template phù hợp, sao chép và điều chỉnh theo yêu cầu người dùng.

BUOC 2 — Quy tắc bắt buộc trong code chart:
- Gọi `matplotlib.use('Agg')` TRƯỚC khi import pyplot (tránh lỗi GUI trên server)
- Gọi `plt.close()` sau khi lưu
- Dòng cuối PHẢI là: `print(f"chart_saved:{chart_path}")` — in đúng format này, KHÔNG in JSON, KHÔNG in dict
- Tên file dùng chữ thường, không dấu, không khoảng trắng

Thư viện ưu tiên: seaborn làm mặc định. Chỉ fallback về matplotlib thuần khi seaborn báo lỗi import.

Ví dụ đúng (dòng cuối):
  chart_path = f"{output_dir}/chart_ten_bieu_do.png"
  plt.savefig(chart_path)
  plt.close()
  print(f"chart_saved:{chart_path}")    # ĐÚNG

Ví dụ SAI — không được làm:
  print({"chart_saved": chart_path})    # SAI — backend không parse được
  print(json.dumps({"chart_saved": chart_path}))  # SAI