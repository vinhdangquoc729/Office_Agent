---
name: slide-creation
description: For the Slide Creator agent only — runs the full 5-step design pipeline to convert a detailed content outline into a PPTX-ready JSON deck
---

# Slide Creation — Design & Generation Pipeline

Receive the `slide_outline` from the analyst and execute the full design pipeline. Do NOT skip steps or take shortcuts — each step informs the next.

Execute all 5 steps in order and produce one JSON output at the end.

---

## Step 1: Content Discovery

Read the `slide_outline` carefully before deciding anything.

1. **Topic & purpose** — What is the central message? What should the audience walk away knowing or doing?
2. **Audience** — Technical level, professional context, expected takeaways
3. **Duration** — Read `slide_outline.estimated_duration` to determine slide count target
4. **Tone** — Infer from content: formal, educational, energetic, analytical
5. **Available assets** — Note any `images[]` paths in sections; note any `metrics[]` data

Build a mental model: what story does this content tell, and to whom?

---

## Step 2: Structure Planning

Map the duration to a slide count and define the deck structure.

| Duration | Slide Count | Structure |
|---|---|---|
| 5 min | 5-7 | Hook → 2-3 key points → CTA |
| 15 min | 12-18 | Intro → 3-4 sections → Summary → CTA |
| 30 min | 25-35 | Title → Agenda → 5-6 sections → Q&A |
| 45 min | 35-50 | Title → Agenda → 7-8 sections → Summary → CTA |

Apply the **one idea per slide** rule. Each slide communicates one concept with supporting evidence.

### Slide Type Vocabulary

Tag every planned slide with a type before generating JSON:

`title`, `section-divider`, `content`, `image-focus`, `comparison`, `quote`, `feature-grid`, `timeline`, `metrics`, `closing`

### Standard deck structure

- Slide 1: `title` (cover)
- Slide 2: `content` (agenda — 3-5 items)
- Per chapter: `section-divider` → 2-4 content slides
- Where data supports: use `metrics`, `comparison`, `timeline`, `feature-grid` instead of plain `content`
- Slide N-1: `content` (conclusion + recommended actions)
- Slide N: `closing` (Q&A, empty bullets)

---

## Step 3: Style Selection

Select one theme from the 12 presets in `style-presets.md` (loaded in your context).

Choose based on audience and content tone:

| Audience / Tone | Recommended preset |
|---|---|
| Corporate, formal | cleanCorporate, midnightBlue |
| Technical, engineering | darkMonospace, terminalGreen |
| Startup, pitch | boldSignal, gradientWave |
| Education, training | warmMinimal, vintageEditorial |
| Creative, marketing | swissModern, darkBotanical |

Commit to one theme. Do not mix themes across slides.

---

## Step 4: Generation

Write TypeScript code that builds the deck slide by slide using PptxGenJS.

### Script skeleton

```typescript
import pptxgen from 'pptxgenjs';
import { createTheme, PRESETS } from './theme.js';
import { addSectionDivider, addSlideNumber, addProgressBar, addStaircase } from './decorative.js';

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';  // 10" × 5.625"

const t = createTheme(PRESETS['<preset from Step 3>']);
const total = <total slide count from Step 2>;

// Image dimension helper — preserves aspect ratio within a bounding box
function fitImage(r: number, maxW: number, maxH: number): { w: number, h: number } {
  return r > maxW / maxH
    ? { w: maxW, h: Math.round(maxW / r * 100) / 100 }
    : { w: Math.round(maxH * r * 100) / 100, h: maxH };
}

// Reusable heading helper — title + accent underline
function heading(slide: any, title: string): void {
  slide.addText(title, { x: 0.5, y: 0.25, w: 9, h: 0.72,
    fontSize: 28, fontFace: t.font.heading, color: t.text.primary, bold: true });
  slide.addShape('line', { x: 0.5, y: 0.97, w: 1.8, h: 0,
    line: { color: t.accent, width: 3 } });
}

// --- slides ---

// cover
{ const s = pptx.addSlide(); s.background = { color: t.bg.primary };
  s.addText('Title', { x: 0.8, y: 1.0, w: 8.4, h: 2.1,
    fontSize: 38, fontFace: t.font.heading, color: t.text.primary, bold: true, align: 'center' });
  s.addText('Subtitle', { x: 1.5, y: 3.3, w: 7, h: 0.85,
    fontSize: 20, fontFace: t.font.body, color: t.text.secondary, align: 'center' });
  s.addNotes('Opening remarks...'); }

// section divider
{ const s = pptx.addSlide();
  addSectionDivider(s, 'Part I: Context', t);
  addProgressBar(s, 2, total, t, { position: 'bottom', height: 0.05 }); }

// bullets
{ const s = pptx.addSlide(); s.background = { color: t.bg.primary };
  heading(s, 'Slide title = key conclusion');
  s.addText([
    { text: 'First point: 8-15 words starting with number or verb', options: {
        bullet: { code: '25B8' }, fontSize: 18, fontFace: t.font.body,
        color: t.text.primary, breakLine: true, paraSpaceAfter: 7 } },
    { text: 'Second point', options: {
        bullet: { code: '25B8' }, fontSize: 18, fontFace: t.font.body,
        color: t.text.primary, breakLine: true, paraSpaceAfter: 7 } },
  ], { x: 0.7, y: 1.15, w: 8.6, h: 3.9, valign: 'top', lineSpacing: 24 });
  addSlideNumber(s, 3, total, t);
  s.addNotes('Speaker talking points 1-3 sentences.'); }

// metrics
{ const s = pptx.addSlide(); s.background = { color: t.bg.primary };
  heading(s, 'Key Numbers Tell the Story');
  const metrics = [{ value: '94%', label: 'Satisfaction rate', unit: 'Q4 2025' }];
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
  addSectionDivider(s, 'Questions & Discussion', t); }

await pptx.writeFile({ fileName: process.argv[2] });
console.log(`OK: ${process.argv[2]}`);
```

### Theme token reference

```
t.bg.primary / t.bg.secondary       background colors
t.text.primary / t.text.secondary   text colors
t.accent / t.accentSecondary        highlight colors
t.font.heading / t.font.body        font face strings
t.spacing.margin                    standard margin (0.5")
t.radius.card                       card corner radius (inches)
```

### Layout patterns

| Slide type | Implementation |
|---|---|
| cover | `addText(title)` centered, large font, `addText(subtitle)` below |
| section_divider | `addSectionDivider(slide, title, t)` from decorative |
| bullets | `heading()` + `addText([...runs], {...})` with `bullet: {code:'25B8'}` |
| metrics | Loop: large `addText(value)` + small `addText(label)` per metric |
| image-focus (1 image) | `heading()` + call `get_image_dimensions` → `fitImage(r, 8.5, 3.8)` → `addImage({ path, x, y:1.15, w, h })` |
| image-focus (2 images) | `heading()` + `get_image_dimensions` for each → `fitImage(r, 4.4, 3.5)` → two `addImage` side by side |
| comparison | Two `addShape('roundRect')` headers + `addText` rows per item |
| timeline | `addShape('line')` spine + `addShape('ellipse')` dots + `addText` above/below |
| feature_grid | Grid of `addShape('roundRect')` cards + `addText(title)` + `addText(desc)` |
| quote | `slide.background = { color: t.accent }` + italic text + attribution |
| closing | `addSectionDivider(slide, 'Q&A', t)` |

### Image handling

**Always call `get_image_dimensions(path)` first**, compute the correct `w`/`h` that fits within the target box, then pass those pre-computed dimensions to `addImage`. This preserves aspect ratio because PptxGenJS renders exactly the `w`/`h` you provide.

**Hard constraint: `y + h` must never exceed 5.5"** (slide height is 5.625"). Always verify before writing.

#### Dimension helper — add this to every script that places images

```typescript
// Paste this function definition into your script (after the imports)
function fitImage(r: number, maxW: number, maxH: number): { w: number, h: number } {
  return r > maxW / maxH
    ? { w: maxW, h: Math.round(maxW / r * 100) / 100 }
    : { w: Math.round(maxH * r * 100) / 100, h: maxH };
}
```

#### Patterns

```typescript
// Pattern A — image-focus slide: heading + full-width image below
// box: maxW=8.5, maxH=3.8  →  y: 1.15, 1.15+3.8=4.95 ✓
const { w: iw, h: ih } = fitImage(aspectRatio, 8.5, 3.8);
s.addImage({ path, x: 0.75 + (8.5 - iw) / 2, y: 1.15, w: iw, h: ih });

// Pattern B — short text + image below (text max 2-3 sentences)
// text h: 1.6  →  image box: maxW=8.5, maxH=2.5, y: 2.9  →  2.9+2.5=5.4 ✓
s.addText([...], { x: 0.7, y: 1.15, w: 8.6, h: 1.6 });
const { w: iw, h: ih } = fitImage(aspectRatio, 8.5, 2.5);
s.addImage({ path, x: 0.75 + (8.5 - iw) / 2, y: 2.9, w: iw, h: ih });

// Pattern C — 2 images side by side
// box each: maxW=4.4, maxH=3.5  →  y: 1.15, 1.15+3.5=4.65 ✓
const d1 = fitImage(r1, 4.4, 3.5);
s.addImage({ path: img1, x: 0.5 + (4.4 - d1.w) / 2, y: 1.15, w: d1.w, h: d1.h });
const d2 = fitImage(r2, 4.4, 3.5);
s.addImage({ path: img2, x: 5.1 + (4.4 - d2.w) / 2, y: 1.15, w: d2.w, h: d2.h });
```

**Prefer Pattern A** over Pattern B. Only combine text + image on one slide when text is 2-3 sentences max.

### Safe imports only

```typescript
import pptxgen from 'pptxgenjs';                         // core API
import { createTheme, PRESETS, resolveFont } from './theme.js';
import { addSectionDivider, addStaircase,
         addSectionBadge, addProgressBar,
         addSlideNumber } from './decorative.js';
```

Do NOT import `layout_builders.js`, `text.js`, `image.js`, `svg.js` — they require `skia-canvas` (native binary that may not be present).

### Tools available during generation

Use these tools to verify exact signatures before writing code:

| Tool | Usage |
|------|-------|
| `get_image_dimensions(path)` | **Call before every `addImage`** — returns `{width, height, aspect_ratio}` to compute correct `w`/`h` |
| `read_script_file("pptx-slides", "theme.ts")` | Verify `PRESETS` keys, `createTheme()`, `SlideTheme` fields |
| `read_script_file("pptx-slides", "decorative.ts")` | Verify `addSectionDivider`, `addProgressBar`, `addSlideNumber` signatures |
| `read_script_file("pptx-slides", "types.ts")` | Inspect `SlideTheme`, `StaircaseOpts`, `ProgressBarOpts` interfaces |
| `read_script_file("pptx-slides", "util.ts")` | Verify `normalizeColor`, `safeOuterShadow` if needed |
| `read_reference("pptx-slides", "pptxgenjs-helpers.md")` | Full API quick-reference with coordinates |
| `load_skill_content("pptx-slides")` | Reload pptx-slides skill overview |

Available script files: `theme.ts`, `decorative.ts`, `types.ts`, `util.ts`, `generate.ts`, `main.ts`
(Do not read: `text.ts`, `image.ts`, `svg.ts`, `layout_builders.ts`, `layout.ts`, `code.ts`, `validation.ts`)

---

## Step 5: Validation

Before outputting the code, self-check:

1. **Slide count** — Does it match the duration target from Step 2?
2. **Speaker notes** — Does every content slide have `slide.addNotes('...')`?
3. **Content density** — Does each slide respect the limits below?
4. **Visual consistency** — Same `t = createTheme(PRESETS['...'])` throughout, no hardcoded colors?
5. **Structure** — Does the deck have: cover → agenda → sections → conclusion → Q&A?
6. **No orphan sections** — Every `addSectionDivider` has at least 1 content slide after it
7. **Safe imports** — No import of `layout_builders.js`, `text.js`, `image.js`, `svg.js`?
8. **Script ends correctly** — `await pptx.writeFile({ fileName: process.argv[2] })` present?

If any check fails, fix before outputting.

---

## Content Density Limits

| Layout | Maximum content |
|---|---|
| cover | 1 title + 1 subtitle + date |
| bullets | 3-6 bullets, each max 15 words |
| section_divider | 1 heading only |
| quote | 1 quote max 40 words + attribution |
| metrics | 2-4 KPIs |
| feature_grid | 3-6 cards, title max 5 words, desc max 15 words |
| comparison | 2 columns, max 5 rows each |
| timeline | 3-6 milestones |
| two_column | Max 80 words per column |

### Auto-split logic

When content from a section exceeds density limits:
- Long bullet lists (>6 items) → split into "Part 1 / Part 2" slides with consistent heading
- Multiple sub-topics in one section → one slide per sub-topic
- Never reduce font size to fit more content — minimum body text is 18pt

---

## Data Visualization

When a section contains charts or graphs, apply these rules:

| Data Type | Use | Avoid |
|---|---|---|
| Comparison | Bar chart | Pie (>5 items) |
| Trend over time | Line chart | Bar (>10 periods) |
| Part of whole | Stacked bar, treemap | Pie (>5 slices) |
| Distribution | Histogram, box plot | Line chart |

**Simplify for slides**: remove gridlines, limit to 3-4 data series, use direct labels instead of legends, highlight the key insight with `t.accent`.

**Progressive disclosure**: if data is complex, split across slides — overview → detail → insight interpretation.

## Design Anti-Patterns

- **Wall of text** — bullets must be 8-15 words, never full paragraphs
- **Font soup** — the theme provides 1 heading + 1 body font; do not override
- **Color rainbow** — use theme tokens only; never hardcode colors
- **Cramming** — split slides rather than fitting everything in one
- **Topic labels as titles** — slide titles must state the conclusion, not the topic
- **Fake images** — only use `images[]` paths that exist in the outline; leave out if none
- **Missing speaker notes** — every content slide must have `notes`
- **Too many layouts** — use 3-4 distinct layout types per deck, not one of each

---


## Related Skills

**`pptx-slides`** — Detailed PptxGenJS design rules that apply to the JSON you output:
- Typography minimums (18pt body, 36-44pt title, 14pt caption floor)
- Color & accessibility rules (WCAG AA contrast, theme tokens only)
- Editability guidance (native text boxes, no flattened text)
- Validation checklist (element overlap, font size floor, bullet count, speaker notes)
