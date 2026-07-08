---
name: slide-creation
description: Dành riêng cho Slide Creator agent — chạy toàn bộ pipeline thiết kế 5 bước để chuyển outline nội dung chi tiết thành JSON deck PPTX
---

# Slide Creation — Pipeline Thiết Kế & Tạo Slide

Nhận `slide_outline` từ analyst và thực hiện toàn bộ pipeline thiết kế. KHÔNG bỏ bước nào — mỗi bước làm cơ sở cho bước sau.

Thực hiện đủ 5 bước theo thứ tự, tạo ra một output JSON duy nhất ở cuối.

---

## Bước 1: Đọc hiểu nội dung

Đọc kỹ `slide_outline` trước khi quyết định bất cứ điều gì.

1. **Chủ đề & mục đích** — Thông điệp trung tâm là gì? Khán giả cần biết hoặc làm gì sau buổi thuyết trình?
2. **Đối tượng** — Trình độ kỹ thuật, bối cảnh nghề nghiệp, kỳ vọng
3. **Thời lượng** — Đọc `slide_outline.estimated_duration` để xác định số slide mục tiêu
4. **Giọng điệu** — Suy luận từ nội dung: trang trọng, học thuật, năng động, phân tích
5. **Tài nguyên có sẵn** — Ghi nhận các `images[]` path trong sections; ghi nhận `metrics[]`

Xây dựng mental model: nội dung kể câu chuyện gì, cho ai?

---

## Bước 2: Lập cấu trúc

Ánh xạ thời lượng sang số slide và xác định cấu trúc deck.

| Thời lượng | Số slide | Cấu trúc |
|---|---|---|
| 5 phút | 5-7 | Hook → 2-3 điểm chính → CTA |
| 15 phút | 12-18 | Mở đầu → 3-4 phần → Tóm tắt → CTA |
| 30 phút | 25-35 | Title → Agenda → 5-6 phần → Q&A |
| 45 phút | 35-50 | Title → Agenda → 7-8 phần → Summary → CTA |

Áp dụng nguyên tắc **1 slide = 1 ý**. Mỗi slide truyền đạt một khái niệm duy nhất.

### Bảng từ vựng loại slide

Gán nhãn loại cho từng slide đã lên kế hoạch trước khi viết JSON:

`title`, `section-divider`, `content`, `image-focus`, `comparison`, `quote`, `feature-grid`, `timeline`, `metrics`, `closing`

### Cấu trúc deck chuẩn

- Slide 1: `title` (bìa)
- Slide 2: `content` (agenda — 3-5 mục)
- Mỗi chương: `section-divider` → 2-4 slide nội dung
- Khi dữ liệu cho phép: dùng `metrics`, `comparison`, `timeline`, `feature-grid` thay cho `content` thông thường
- Slide N-1: `content` (kết luận + đề xuất hành động)
- Slide N: `closing` (Q&A, bullets rỗng)

---

## Bước 3: Chọn style

Chọn một theme từ 12 preset trong `style-presets.md` (đã load trong context của bạn).

Chọn dựa trên đối tượng và giọng điệu nội dung:

| Đối tượng / Giọng điệu | Preset khuyến nghị |
|---|---|
| Doanh nghiệp, trang trọng | cleanCorporate, midnightBlue |
| Kỹ thuật, lập trình | darkMonospace, terminalGreen |
| Startup, gọi vốn | boldSignal, gradientWave |
| Giáo dục, đào tạo | warmMinimal, vintageEditorial |
| Sáng tạo, marketing | swissModern, darkBotanical |

Chỉ dùng 1 theme duy nhất. Không trộn theme giữa các slide.

---

## Bước 4: Tạo slides

Viết TypeScript code xây dựng deck từng slide bằng PptxGenJS.

### Skeleton script

```typescript
import pptxgen from 'pptxgenjs';
import { createTheme, PRESETS } from './theme.js';
import { addSectionDivider, addSlideNumber, addProgressBar, addStaircase } from './decorative.js';

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';  // 10" × 5.625"

const t = createTheme(PRESETS['<preset từ Bước 3>']);
const total = <tổng số slide từ Bước 2>;

// Helper heading: tiêu đề + gạch chân accent
function heading(slide: any, title: string): void {
  slide.addText(title, { x: 0.5, y: 0.25, w: 9, h: 0.72,
    fontSize: 28, fontFace: t.font.heading, color: t.text.primary, bold: true });
  slide.addShape('line', { x: 0.5, y: 0.97, w: 1.8, h: 0,
    line: { color: t.accent, width: 3 } });
}

// --- các slide ---

// bìa
{ const s = pptx.addSlide(); s.background = { color: t.bg.primary };
  s.addText('Tiêu đề', { x: 0.8, y: 1.0, w: 8.4, h: 2.1,
    fontSize: 38, fontFace: t.font.heading, color: t.text.primary, bold: true, align: 'center' });
  s.addText('Phụ đề', { x: 1.5, y: 3.3, w: 7, h: 0.85,
    fontSize: 20, fontFace: t.font.body, color: t.text.secondary, align: 'center' });
  s.addNotes('Mở đầu bài thuyết trình...'); }

// section divider
{ const s = pptx.addSlide();
  addSectionDivider(s, 'Phần I: Bối cảnh', t);
  addProgressBar(s, 2, total, t, { position: 'bottom', height: 0.05 }); }

// bullets
{ const s = pptx.addSlide(); s.background = { color: t.bg.primary };
  heading(s, 'Tiêu đề slide = kết luận chính');
  s.addText([
    { text: 'Điểm 1: 8-15 từ, bắt đầu bằng số hoặc động từ', options: {
        bullet: { code: '25B8' }, fontSize: 18, fontFace: t.font.body,
        color: t.text.primary, breakLine: true, paraSpaceAfter: 7 } },
    { text: 'Điểm 2', options: {
        bullet: { code: '25B8' }, fontSize: 18, fontFace: t.font.body,
        color: t.text.primary, breakLine: true, paraSpaceAfter: 7 } },
  ], { x: 0.7, y: 1.15, w: 8.6, h: 3.9, valign: 'top', lineSpacing: 24 });
  addSlideNumber(s, 3, total, t);
  s.addNotes('Gợi ý thuyết trình 1-3 câu.'); }

// metrics
{ const s = pptx.addSlide(); s.background = { color: t.bg.primary };
  heading(s, 'Số liệu nói lên câu chuyện');
  const metrics = [{ value: '94%', label: 'Tỷ lệ hài lòng', unit: 'Q4 2025' }];
  const mW = 9 / metrics.length;
  metrics.forEach((m, i) => {
    const cx = 0.5 + i * mW;
    s.addText(m.value, { x: cx, y: 1.4, w: mW, h: 1.5,
      fontSize: 48, fontFace: t.font.heading, color: t.accent, bold: true, align: 'center', valign: 'bottom' });
    s.addText(m.label, { x: cx, y: 2.95, w: mW, h: 0.5,
      fontSize: 18, fontFace: t.font.body, color: t.text.primary, align: 'center' });
    if (m.unit) s.addText(m.unit, { x: cx, y: 3.5, w: mW, h: 0.35,
      fontSize: 14, fontFace: t.font.body, color: t.text.secondary, align: 'center' });
  });
  addSlideNumber(s, 4, total, t); s.addNotes('...'); }

// closing / Q&A
{ const s = pptx.addSlide();
  addSectionDivider(s, 'Câu hỏi & Thảo luận', t); }

await pptx.writeFile({ fileName: process.argv[2] });
console.log(`OK: ${process.argv[2]}`);
```

### Theme token

```
t.bg.primary / t.bg.secondary       màu nền
t.text.primary / t.text.secondary   màu chữ
t.accent / t.accentSecondary        màu nhấn
t.font.heading / t.font.body        font face
t.spacing.margin                    margin chuẩn (0.5")
t.radius.card                       bo góc card (inches)
```

### Patterns theo loại slide

| Loại slide | Cách code |
|---|---|
| cover | `addText(title)` căn giữa, fontSize lớn |
| section_divider | `addSectionDivider(slide, title, t)` |
| bullets | `heading()` + `addText([...runs], {...})` với `bullet:{code:'25B8'}` |
| metrics | Loop: `addText(value)` lớn + `addText(label)` nhỏ |
| image-focus (1 ảnh) | `heading()` + `addImage({ path, x: 0.75, y: 1.15, w: 8.5, h: 3.8, sizing: { type: 'contain', w: 8.5, h: 3.8 } })` |
| image-focus (2 ảnh) | `heading()` + 2 `addImage` ngang nhau: trái `x:0.5 w:4.4`, phải `x:5.1 w:4.4`, cả hai `h:3.5 sizing:{type:'contain',...}` |
| comparison | 2 header `addShape('roundRect')` + `addText` rows |
| timeline | `addShape('line')` trục + `addShape('ellipse')` chấm + text |
| feature_grid | Lưới `addShape('roundRect')` + `addText(title)` + `addText(desc)` |
| quote | `slide.background = { color: t.accent }` + chữ nghiêng + attribution |
| closing | `addSectionDivider(slide, 'Q&A', t)` |

### Xử lý ảnh

**Luôn dùng `sizing: { type: 'contain', w, h }` — không bao giờ bỏ qua.** Nếu không có `sizing`, PptxGenJS kéo giãn ảnh theo đúng `w`/`h` chỉ định, làm méo tỉ lệ.

**Ràng buộc cứng: `y + h` không được vượt quá 5.5"** (slide cao 5.625"). Luôn kiểm tra trước khi viết.

```typescript
// Pattern A — image-focus slide: heading + ảnh (không có text body)
s.addImage({
  path: '/đường/dẫn/tuyệt/đối/image.png',
  x: 0.75, y: 1.15, w: 8.5, h: 3.8,   // 1.15 + 3.8 = 4.95 ✓
  sizing: { type: 'contain', w: 8.5, h: 3.8 },
});

// Pattern B — text ngắn + ảnh cùng slide
s.addText([...], { x: 0.7, y: 1.15, w: 8.6, h: 1.6 });          // text box ngắn
s.addImage({ path: img, x: 0.75, y: 2.9, w: 8.5, h: 2.5,        // 2.9 + 2.5 = 5.4 ✓
  sizing: { type: 'contain', w: 8.5, h: 2.5 } });

// Pattern C — 2 ảnh ngang nhau bên dưới heading
s.addImage({ path: img1, x: 0.5, y: 1.15, w: 4.4, h: 3.5,       // 1.15 + 3.5 = 4.65 ✓
  sizing: { type: 'contain', w: 4.4, h: 3.5 } });
s.addImage({ path: img2, x: 5.1, y: 1.15, w: 4.4, h: 3.5,
  sizing: { type: 'contain', w: 4.4, h: 3.5 } });
```

**Ưu tiên Pattern A** (slide image-focus riêng). Chỉ dùng Pattern B khi text thực sự ngắn (2-3 câu).

### Import an toàn

```typescript
import pptxgen from 'pptxgenjs';
import { createTheme, PRESETS, resolveFont } from './theme.js';
import { addSectionDivider, addStaircase,
         addSectionBadge, addProgressBar,
         addSlideNumber } from './decorative.js';
```

KHÔNG import `layout_builders.js`, `text.js`, `image.js`, `svg.js` — chúng cần `skia-canvas` (native binary có thể không có sẵn).

### Tools có thể dùng khi viết code

Dùng để kiểm tra signature chính xác trước khi viết:

| Tool | Dùng để |
|------|---------|
| `read_script_file("pptx-slides", "theme.ts")` | Xem `PRESETS` keys, `createTheme()`, fields của `SlideTheme` |
| `read_script_file("pptx-slides", "decorative.ts")` | Xem signature của `addSectionDivider`, `addProgressBar`, `addSlideNumber` |
| `read_script_file("pptx-slides", "types.ts")` | Xem interfaces `SlideTheme`, `StaircaseOpts`, `ProgressBarOpts` |
| `read_script_file("pptx-slides", "util.ts")` | Xem `normalizeColor`, `safeOuterShadow` nếu cần |
| `read_reference("pptx-slides", "pptxgenjs-helpers.md")` | API quick-reference đầy đủ với tọa độ layout |
| `load_skill_content("pptx-slides")` | Load lại skill overview pptx-slides |

File script có sẵn: `theme.ts`, `decorative.ts`, `types.ts`, `util.ts`, `generate.ts`, `main.ts`
(Không đọc: `text.ts`, `image.ts`, `svg.ts`, `layout_builders.ts`, `layout.ts`, `code.ts`, `validation.ts`)

---

## Bước 5: Kiểm tra

Trước khi xuất code, tự kiểm tra:

1. **Số slide** — Có đúng với mục tiêu thời lượng từ Bước 2 không?
2. **Speaker notes** — Mọi slide nội dung có `slide.addNotes('...')` không?
3. **Mật độ nội dung** — Mỗi slide có tuân giới hạn bên dưới không?
4. **Nhất quán thị giác** — Cùng 1 `t = createTheme(PRESETS['...'])`, không hardcode màu?
5. **Cấu trúc** — Deck có đủ: bìa → agenda → các phần → kết luận → Q&A không?
6. **Không có section cô đơn** — Mỗi `addSectionDivider` có ít nhất 1 slide nội dung theo sau không?
7. **Import an toàn** — Không import `layout_builders.js`, `text.js`, `image.js`, `svg.js`?
8. **Script kết thúc đúng** — Có `await pptx.writeFile({ fileName: process.argv[2] })` không?

Nếu bất kỳ điều nào không đạt, sửa trước khi xuất.

---

## Giới hạn mật độ nội dung

| Layout | Giới hạn |
|---|---|
| cover | 1 title + 1 subtitle + date |
| bullets | 3-6 bullets, mỗi bullet tối đa 15 từ |
| section_divider | 1 heading duy nhất |
| quote | 1 trích dẫn tối đa 40 từ + attribution |
| metrics | 2-4 chỉ số |
| feature_grid | 3-6 cards, title tối đa 5 từ, desc tối đa 15 từ |
| comparison | 2 cột, tối đa 5 dòng mỗi cột |
| timeline | 3-6 mốc |
| two_column | Tối đa 80 từ mỗi cột |

### Logic tách slide

Khi nội dung của một section vượt giới hạn:
- Danh sách bullet dài (>6 điểm) → tách thành "Phần 1 / Phần 2" với heading nhất quán
- Nhiều chủ đề con trong một section → mỗi chủ đề con một slide
- Không bao giờ giảm cỡ chữ để nhét thêm nội dung — cỡ chữ tối thiểu 18pt

---

## Trực quan hóa dữ liệu

Khi section chứa biểu đồ hoặc đồ thị:

| Loại dữ liệu | Dùng | Tránh |
|---|---|---|
| So sánh | Bar chart | Pie (>5 mục) |
| Xu hướng theo thời gian | Line chart | Bar (>10 kỳ) |
| Phần của tổng thể | Stacked bar, treemap | Pie (>5 phần) |
| Phân phối | Histogram, box plot | Line chart |

**Đơn giản hóa cho slide**: bỏ gridlines, tối đa 3-4 data series, dùng label trực tiếp thay legend, highlight insight chính bằng `t.accent`.

**Progressive disclosure**: nếu dữ liệu phức tạp, tách thành nhiều slide — tổng quan → chi tiết → giải thích insight.

## Anti-patterns cần tránh

- **Wall of text** — bullet phải 8-15 từ, không bao giờ là đoạn văn
- **Font soup** — theme cung cấp 1 font heading + 1 font body; không override
- **Hardcode màu** — chỉ dùng token của theme, không hardcode hex
- **Cramming** — tách slide thay vì nhét hết vào 1 slide
- **Nhãn chủ đề làm tiêu đề** — tiêu đề phải là kết luận, không phải nhãn
- **Fake images** — chỉ dùng `images[]` path có thực từ outline
- **Thiếu speaker notes** — mọi slide nội dung phải có `notes`
- **Quá nhiều layout** — dùng 3-4 loại layout trong 1 deck là đủ

---


## Skill liên quan

**`pptx-slides`** — Design rules chi tiết của PptxGenJS áp dụng cho JSON bạn xuất ra:
- Cỡ chữ tối thiểu (18pt body, 36-44pt title, 14pt caption)
- Màu sắc & accessibility (WCAG AA contrast, chỉ dùng theme tokens)
- Hướng dẫn editability (native text boxes, không flatten text thành ảnh)
- Validation checklist (overlap, font size floor, số bullet, speaker notes)
