# Chart Templates

Các template dưới đây dùng seaborn làm mặc định. Mỗi template đã bao gồm đầy đủ: thiết lập style, màu sắc, font, nhãn trục, title, và lưu file. Sao chép và thay thế tên biến/cột là dùng được ngay.

Timestamp được backend tự thêm vào tên file — không cần import time trong code.

---

## Thiết lập chung (chạy một lần ở đầu script)

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
```

---

## 1. Bar Chart — So sánh giá trị giữa các nhóm

Dùng khi: so sánh điểm, doanh thu, số lượng theo danh mục.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)

# df phải có cột nhãn (category) và cột giá trị (value)
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=df, x='ten_cot_nhan', y='ten_cot_gia_tri', ax=ax,
            order=df.groupby('ten_cot_nhan')['ten_cot_gia_tri'].mean().sort_values(ascending=False).index)

ax.set_title('Tiêu đề biểu đồ', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Nhãn trục X', fontsize=11)
ax.set_ylabel('Nhãn trục Y', fontsize=11)
ax.tick_params(axis='x', rotation=45)

# Ghi giá trị lên từng cột
for bar in ax.patches:
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01 * ax.get_ylim()[1],
            f'{bar.get_height():.1f}',
            ha='center', va='bottom', fontsize=9)

plt.tight_layout()
chart_path = f"{output_dir}/chart_bar.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 2. Horizontal Bar Chart — Khi nhãn dài

Dùng khi: tên sinh viên, tên môn học, tên sản phẩm dài.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', palette='Blues_d', font_scale=1.1)

df_sorted = df.sort_values('ten_cot_gia_tri', ascending=True).tail(20)

fig, ax = plt.subplots(figsize=(10, max(6, len(df_sorted) * 0.4)))
sns.barplot(data=df_sorted, y='ten_cot_nhan', x='ten_cot_gia_tri', ax=ax, orient='h')

ax.set_title('Tiêu đề biểu đồ', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Nhãn trục X', fontsize=11)
ax.set_ylabel('', fontsize=11)
ax.axvline(df['ten_cot_gia_tri'].mean(), color='red', linestyle='--', linewidth=1.2, label='Trung bình')
ax.legend(fontsize=10)

plt.tight_layout()
chart_path = f"{output_dir}/chart_hbar.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 3. Line Chart — Xu hướng theo thời gian

Dùng khi: xu hướng doanh thu, điểm theo tuần, số lượng theo tháng.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', font_scale=1.1)

fig, ax = plt.subplots(figsize=(12, 5))
sns.lineplot(data=df, x='ten_cot_thoi_gian', y='ten_cot_gia_tri',
             marker='o', linewidth=2.5, markersize=7, ax=ax)

ax.set_title('Tiêu đề biểu đồ', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Thời gian', fontsize=11)
ax.set_ylabel('Giá trị', fontsize=11)
ax.tick_params(axis='x', rotation=45)

# Ghi giá trị tại mỗi điểm
for x_val, y_val in zip(df['ten_cot_thoi_gian'], df['ten_cot_gia_tri']):
    ax.annotate(f'{y_val:.1f}', (x_val, y_val),
                textcoords='offset points', xytext=(0, 8),
                ha='center', fontsize=8)

plt.tight_layout()
chart_path = f"{output_dir}/chart_line.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 4. Histogram — Phân phối dữ liệu số

Dùng khi: phân phối điểm số, phân phối doanh thu, kiểm tra độ lệch dữ liệu.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', font_scale=1.1)

fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(df['ten_cot'], bins=20, kde=True, ax=ax, color='steelblue')

mean_val = df['ten_cot'].mean()
ax.axvline(mean_val, color='red', linestyle='--', linewidth=1.5,
           label=f'Trung bình: {mean_val:.2f}')
ax.legend(fontsize=10)

ax.set_title('Phân phối — Tên cột', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Giá trị', fontsize=11)
ax.set_ylabel('Số lượng', fontsize=11)

plt.tight_layout()
chart_path = f"{output_dir}/chart_hist.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 5. Pie / Donut Chart — Tỷ lệ phần trăm

Dùng khi: tỷ lệ loại, tỷ lệ đạt/không đạt, phân bổ danh mục.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

counts = df['ten_cot_phan_loai'].value_counts()
colors = plt.cm.Pastel1.colors[:len(counts)]

fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    counts.values,
    labels=counts.index,
    autopct='%1.1f%%',
    colors=colors,
    startangle=140,
    wedgeprops=dict(width=0.6),   # width < 1 → donut; bỏ dòng này → pie thường
    pctdistance=0.75
)
for text in autotexts:
    text.set_fontsize(10)
    text.set_fontweight('bold')

ax.set_title('Tiêu đề biểu đồ', fontsize=14, fontweight='bold', pad=20)
ax.legend(wedges, [f'{l}: {v}' for l, v in zip(counts.index, counts.values)],
          loc='lower right', fontsize=9)

plt.tight_layout()
chart_path = f"{output_dir}/chart_pie.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 6. Scatter Plot — Tương quan hai biến

Dùng khi: điểm quá trình vs điểm thi, doanh thu vs chi phí.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style='whitegrid', font_scale=1.1)

fig, ax = plt.subplots(figsize=(8, 6))
sns.scatterplot(data=df, x='ten_cot_x', y='ten_cot_y', alpha=0.7, ax=ax)

# Đường trendline
m, b = np.polyfit(df['ten_cot_x'].dropna(), df['ten_cot_y'].dropna(), 1)
x_range = np.linspace(df['ten_cot_x'].min(), df['ten_cot_x'].max(), 100)
ax.plot(x_range, m * x_range + b, color='red', linewidth=1.5, linestyle='--', label='Trendline')
ax.legend(fontsize=10)

ax.set_title('Tương quan — X vs Y', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Tên cột X', fontsize=11)
ax.set_ylabel('Tên cột Y', fontsize=11)

plt.tight_layout()
chart_path = f"{output_dir}/chart_scatter.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 7. Boxplot — Phân phối theo nhóm và phát hiện outlier

Dùng khi: so sánh phân phối điểm giữa các lớp, phân phối doanh thu theo tháng.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', palette='Set2', font_scale=1.1)

fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df, x='ten_cot_nhom', y='ten_cot_gia_tri', ax=ax)
sns.stripplot(data=df, x='ten_cot_nhom', y='ten_cot_gia_tri',
              color='black', alpha=0.3, size=3, ax=ax)

ax.set_title('Phân phối theo nhóm', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Nhóm', fontsize=11)
ax.set_ylabel('Giá trị', fontsize=11)
ax.tick_params(axis='x', rotation=30)

plt.tight_layout()
chart_path = f"{output_dir}/chart_box.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```

---

## 8. Heatmap — Ma trận tương quan hoặc bảng chéo

Dùng khi: correlation matrix, bảng điểm nhiều môn theo nhiều tuần.

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(font_scale=1.0)

# Dùng correlation matrix
corr = df.select_dtypes('number').corr()

fig, ax = plt.subplots(figsize=(max(8, len(corr) * 0.8), max(6, len(corr) * 0.7)))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            linewidths=0.5, ax=ax, square=True,
            cbar_kws={'shrink': 0.8})

ax.set_title('Ma trận tương quan', fontsize=14, fontweight='bold', pad=15)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)

plt.tight_layout()
chart_path = f"{output_dir}/chart_heatmap.png"
plt.savefig(chart_path)
plt.close()
print(f"chart_saved:{chart_path}")
```
