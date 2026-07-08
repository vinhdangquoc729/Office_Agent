# PptxGenJS Helpers — API Reference

## Safe imports

```typescript
import pptxgen from 'pptxgenjs';
import { createTheme, PRESETS, resolveFont, sectionBackground } from './theme.js';
import { addStaircase, addSectionBadge, addProgressBar,
         addSlideNumber, addSectionDivider } from './decorative.js';
```

Do NOT import `layout_builders.js`, `text.js`, `image.js`, `svg.js` — require `skia-canvas`.

---

## Theme

### `PRESETS` — available keys

`darkMonospace`, `swissModern`, `boldSignal`, `darkBotanical`, `cleanCorporate`,
`neonCyber`, `warmMinimal`, `vintageEditorial`, `terminalGreen`, `gradientWave`,
`midnightBlue`, `paperInk`

### `createTheme(preset)` → `SlideTheme`

```typescript
const t = createTheme(PRESETS['cleanCorporate']);
```

### `SlideTheme` fields

```typescript
t.bg.primary          // main background hex (no #)
t.bg.secondary        // card / surface hex
t.text.primary        // body text hex
t.text.secondary      // muted text hex
t.accent              // highlight color hex
t.accentSecondary     // secondary highlight hex
t.font.heading        // heading font name (e.g. 'Plus Jakarta Sans')
t.font.body           // body font name (e.g. 'Source Sans 3')
t.font.mono           // mono font name
t.size.title.min/max  // title font size range [36,44]
t.size.heading.min/max// heading font size range [28,36]
t.size.body.min/max   // body font size range [18,24]
t.size.caption.min/max// caption font size range [14,16]
t.spacing.margin      // side margin in inches (0.5)
t.spacing.gutter      // gutter between elements (0.3)
t.spacing.cardPad     // card internal padding (0.2)
t.radius.card         // card corner radius in inches (0.1)
t.radius.badge        // badge corner radius (0.05)
```

### `resolveFont(theme, role)` → string

```typescript
resolveFont(t, 'heading')  // → 'Plus Jakarta Sans, Arial'
resolveFont(t, 'body')     // → 'Source Sans 3, Arial'
resolveFont(t, 'mono')     // → 'Consolas, Consolas'
```

### `sectionBackground(slideIndex, sectionMap, colors)` → hex

```typescript
const sectionMap = { '0': 'brand', '1-3': 'light', '4-8': 'default' };
const colors = { brand: t.accent, light: t.bg.secondary, default: t.bg.primary };
slide.background = { color: sectionBackground(i, sectionMap, colors) };
```

---

## Decorative helpers

All helpers take `(slide: any, ...opts, theme: SlideTheme)`.

### `addSectionDivider(slide, title, theme)`

Full-bleed accent background with centered title. Use for chapter breaks.

```typescript
addSectionDivider(slide, 'Part II: Results', t);
```

### `addProgressBar(slide, current, total, theme, opts?)`

Thin progress bar showing deck position.

```typescript
addProgressBar(slide, 3, total, t, { position: 'bottom', height: 0.05 });
// opts.position: 'top' | 'bottom' (default 'bottom')
// opts.height: bar height in inches (default 0.05)
```

### `addSlideNumber(slide, current, total, theme)`

Slide counter in bottom-right corner (e.g. "3 / 12").

```typescript
addSlideNumber(slide, 3, total, t);
```

### `addStaircase(slide, opts?)`

Decorative staircase shape for visual texture.

```typescript
addStaircase(slide, {
  position: 'bottom-right',  // 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  color: t.accent,
  steps: 4,
  stepWidth: 0.4,
  stepHeight: 0.3,
  opacity: 0.15,
});
```

### `addSectionBadge(slide, text, opts?)`

Small pill badge. Useful for category labels.

```typescript
addSectionBadge(slide, 'Section 1', { x: 0.5, y: 0.1, theme: t });
```

---

## PptxGenJS core API

### Slide dimensions: 10" × 5.625" (16:9)

### `pptx.addSlide()` → slide

```typescript
const slide = pptx.addSlide();
slide.background = { color: t.bg.primary };  // hex without #
```

### `slide.addText(text, opts)` — single string

```typescript
slide.addText('Hello', {
  x: 0.5, y: 0.25, w: 9, h: 0.72,
  fontSize: 28,          // pt — minimum 18pt body, 14pt caption
  fontFace: t.font.heading,
  color: t.text.primary, // hex without #
  bold: true,
  italic: false,
  align: 'left',         // 'left' | 'center' | 'right'
  valign: 'top',         // 'top' | 'middle' | 'bottom'
  lineSpacing: 32,       // pt
  wrap: true,
});
```

### `slide.addText(runs, opts)` — rich text runs

```typescript
slide.addText([
  { text: 'First bullet', options: {
      bullet: { code: '25B8' },   // ▸ filled right triangle
      fontSize: 18, fontFace: t.font.body, color: t.text.primary,
      breakLine: true, paraSpaceAfter: 7,
  }},
  { text: 'Second bullet', options: {
      bullet: { code: '25B8' },
      fontSize: 18, fontFace: t.font.body, color: t.text.primary,
      breakLine: true, paraSpaceAfter: 7,
  }},
], { x: 0.7, y: 1.15, w: 8.6, h: 3.9, valign: 'top', lineSpacing: 24 });
```

Common bullet codes: `25B8` (▸), `2022` (•), `25CF` (●), `2013` (–)

### `slide.addShape(type, opts)`

```typescript
// Rectangle
slide.addShape('rect', {
  x: 0.5, y: 1.0, w: 4.0, h: 0.5,
  fill: { color: t.accent },
  line: { color: t.accent, width: 1 },  // omit for no border
});

// Rounded rectangle
slide.addShape('roundRect', {
  x: 0.5, y: 1.0, w: 4.0, h: 1.5,
  rectRadius: t.radius.card,
  fill: { color: t.bg.secondary },
});

// Line
slide.addShape('line', {
  x: 0.5, y: 1.0, w: 3.0, h: 0,
  line: { color: t.accent, width: 3 },
});

// Ellipse (dot)
slide.addShape('ellipse', {
  x: 1.0, y: 2.0, w: 0.18, h: 0.18,
  fill: { color: t.accent },
});
```

### `slide.addImage(opts)`

```typescript
slide.addImage({
  path: '/absolute/path/to/image.png',  // must exist
  x: 0.5, y: 1.0, w: 4.0, h: 3.0,
  sizing: { type: 'contain', w: 4.0, h: 3.0 },
  // type: 'crop' | 'contain' | 'cover'
});
```

### `slide.addNotes(text)`

```typescript
slide.addNotes('Speaker talking points. 1-3 sentences max.');
```

Required on every content slide.

---

## Typography rules

| Usage | Font size |
|-------|-----------|
| Cover title | 36-44pt |
| Section heading | 28-36pt |
| Body / bullet | 18-24pt (minimum 18pt) |
| Caption / footnote | 14-16pt (minimum 14pt) |
| Slide number | 11-12pt |

Never reduce font size to fit more content — split into multiple slides instead.

---

## Layout reference coordinates (10" × 5.625")

| Region | x | y | w | h |
|--------|---|---|---|---|
| Full slide | 0 | 0 | 10 | 5.625 |
| Safe area | 0.5 | 0.25 | 9 | 5.125 |
| Heading row | 0.5 | 0.25 | 9 | 0.72 |
| Accent line | 0.5 | 0.97 | 1.8 | 0 |
| Content area | 0.7 | 1.15 | 8.6 | 3.9 |
| Left half | 0.5 | 1.15 | 4.3 | 3.9 |
| Right half | 5.2 | 1.15 | 4.3 | 3.9 |
| Footer | 0.5 | 5.2 | 9 | 0.3 |
