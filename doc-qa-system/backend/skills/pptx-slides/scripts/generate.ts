#!/usr/bin/env node
/**
 * generate.ts — Bridge script: JSON slide spec → .pptx via PptxGenJS
 *
 * Usage: npx tsx generate.ts <input.json> <output.pptx>
 *
 * JSON spec schema:
 * {
 *   "theme": "cleanCorporate",   // optional, one of 12 presets
 *   "slides": [ ...SlideSpec ]
 * }
 *
 * Layout types: cover, section_divider, bullets, quote, metrics,
 *               feature_grid, comparison, timeline, two_column,
 *               images, bullets_image1, bullets_image2, image_text
 */

// @ts-ignore — pptxgenjs types don't expose construct signatures in ESM context
import pptxgen from 'pptxgenjs';
import { PRESETS, createTheme } from './theme.js';
import { addSectionDivider, addStaircase, addSlideNumber, addProgressBar } from './decorative.js';
import type { SlideTheme } from './types.js';
import { readFileSync, existsSync } from 'node:fs';

// ─── Inlined layout builders (avoids importing text.ts / skia-canvas) ────────

function addFeatureGrid(slide: any, features: any[], region: any, theme: SlideTheme): void {
  const { x, y, w, h } = region;
  const cols = Math.min(features.length, 3);
  const rows = Math.ceil(features.length / cols);
  const cardW = (w - (cols - 1) * 0.2) / cols;
  const cardH = (h - (rows - 1) * 0.15) / rows;
  features.forEach((feat: any, i: number) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const cx = x + col * (cardW + 0.2);
    const cy = y + row * (cardH + 0.15);
    slide.addShape('roundRect', {
      x: cx, y: cy, w: cardW, h: cardH,
      fill: { color: theme.bg.secondary },
      rectRadius: theme.radius.card,
    });
    slide.addText(feat.title || '', {
      x: cx + 0.15, y: cy + 0.1, w: cardW - 0.3, h: 0.4,
      fontSize: 15, fontFace: theme.font.heading,
      color: theme.text.primary, bold: true, valign: 'top',
    });
    slide.addText(feat.desc || feat.description || '', {
      x: cx + 0.15, y: cy + 0.55, w: cardW - 0.3, h: cardH - 0.7,
      fontSize: 12, fontFace: theme.font.body,
      color: theme.text.secondary, valign: 'top',
    });
  });
}

function addComparisonTable(slide: any, data: any, region: any, theme: SlideTheme): void {
  const { x, y, w, h } = region;
  const colW = (w - 0.3) / 2;
  slide.addShape('roundRect', {
    x, y, w: colW, h: 0.5, fill: { color: theme.accent }, rectRadius: theme.radius.card,
  });
  slide.addText(data.leftHeader || 'Before', {
    x, y, w: colW, h: 0.5, fontSize: 15, fontFace: theme.font.heading,
    color: 'ffffff', bold: true, align: 'center', valign: 'middle',
  });
  slide.addShape('roundRect', {
    x: x + colW + 0.3, y, w: colW, h: 0.5,
    fill: { color: theme.accentSecondary || theme.accent }, rectRadius: theme.radius.card,
  });
  slide.addText(data.rightHeader || 'After', {
    x: x + colW + 0.3, y, w: colW, h: 0.5, fontSize: 15, fontFace: theme.font.heading,
    color: 'ffffff', bold: true, align: 'center', valign: 'middle',
  });
  const items: any[] = data.items || [];
  const rowH = Math.min((h - 0.7) / Math.max(items.length, 1), 0.6);
  items.forEach((item: any, i: number) => {
    const ry = y + 0.6 + i * (rowH + 0.05);
    slide.addText(item.left || '', {
      x, y: ry, w: colW, h: rowH, fontSize: 13, fontFace: theme.font.body,
      color: theme.text.primary, valign: 'middle',
    });
    slide.addText(item.right || '', {
      x: x + colW + 0.3, y: ry, w: colW, h: rowH, fontSize: 13, fontFace: theme.font.body,
      color: theme.text.primary, valign: 'middle',
    });
  });
}

function addMetricsRow(slide: any, metrics: any[], region: any, theme: SlideTheme): void {
  const { x, y, w, h } = region;
  const count = metrics.length;
  const cardW = (w - (count - 1) * 0.2) / count;
  metrics.forEach((metric: any, i: number) => {
    const cx = x + i * (cardW + 0.2);
    slide.addText(String(metric.value), {
      x: cx, y, w: cardW, h: h * 0.55,
      fontSize: 40, fontFace: theme.font.heading,
      color: theme.accent, bold: true, align: 'center', valign: 'bottom',
    });
    slide.addText(metric.label || '', {
      x: cx, y: y + h * 0.55, w: cardW, h: h * 0.25,
      fontSize: 14, fontFace: theme.font.body,
      color: theme.text.primary, align: 'center', valign: 'top',
    });
    if (metric.unit) {
      slide.addText(metric.unit, {
        x: cx, y: y + h * 0.8, w: cardW, h: h * 0.2,
        fontSize: 11, fontFace: theme.font.body,
        color: theme.text.secondary, align: 'center', valign: 'top',
      });
    }
  });
}

function addTimeline(slide: any, milestones: any[], region: any, theme: SlideTheme): void {
  const { x, y, w, h } = region;
  const count = milestones.length;
  const segW = w / count;
  const lineY = y + h * 0.4;
  slide.addShape('line', {
    x, y: lineY, w, h: 0, line: { color: theme.text.secondary, width: 2 },
  });
  milestones.forEach((ms: any, i: number) => {
    const cx = x + i * segW + segW / 2;
    slide.addShape('ellipse', {
      x: cx - 0.09, y: lineY - 0.09, w: 0.18, h: 0.18, fill: { color: theme.accent },
    });
    slide.addText(ms.date || '', {
      x: cx - segW / 2, y, w: segW, h: h * 0.35,
      fontSize: 11, fontFace: theme.font.body, color: theme.text.secondary,
      align: 'center', valign: 'bottom',
    });
    slide.addText(ms.title || '', {
      x: cx - segW / 2, y: lineY + 0.18, w: segW, h: h * 0.45,
      fontSize: 13, fontFace: theme.font.body, color: theme.text.primary,
      align: 'center', valign: 'top',
    });
  });
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function addHeading(slide: any, title: string, theme: SlideTheme): void {
  slide.addText(title, {
    x: 0.5, y: 0.25, w: 9, h: 0.72,
    fontSize: 28, fontFace: theme.font.heading,
    color: theme.text.primary, bold: true,
  });
  slide.addShape('line', {
    x: 0.5, y: 0.97, w: 1.8, h: 0, line: { color: theme.accent, width: 3 },
  });
}

function safeImage(slide: any, imgPath: string, opts: any): void {
  if (imgPath && existsSync(imgPath)) {
    slide.addImage({ path: imgPath, ...opts });
  } else {
    // Placeholder rect
    slide.addShape('rect', {
      x: opts.x, y: opts.y, w: opts.w, h: opts.h,
      fill: { color: 'eeeeee' }, line: { color: 'cccccc', width: 1 },
    });
    slide.addText('[Hình ảnh]', {
      x: opts.x, y: opts.y, w: opts.w, h: opts.h,
      fontSize: 13, fontFace: theme.font.body, color: '999999',
      align: 'center', valign: 'middle',
    });
  }
}

let theme: SlideTheme; // set in main, used in safeImage fallback

// ─── Layout renderers ─────────────────────────────────────────────────────────

function renderCover(prs: any, data: any, t: SlideTheme, _idx: number, _total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  slide.addShape('rect', { x: 0, y: 0, w: 10, h: 0.07, fill: { color: t.accent } });
  slide.addShape('rect', { x: 0, y: 5.555, w: 10, h: 0.07, fill: { color: t.accent } });

  slide.addText(data.title || '', {
    x: 0.8, y: 1.0, w: 8.4, h: 2.1,
    fontSize: 38, fontFace: t.font.heading, color: t.text.primary,
    bold: true, align: 'center', lineSpacing: 46,
  });
  if (data.subtitle) {
    slide.addText(data.subtitle, {
      x: 1.5, y: 3.3, w: 7, h: 0.85,
      fontSize: 20, fontFace: t.font.body, color: t.text.secondary,
      align: 'center',
    });
  }
  const footer = [data.date].filter(Boolean).join(' — ');
  if (footer) {
    slide.addText(footer, {
      x: 1, y: 4.7, w: 8, h: 0.4,
      fontSize: 13, fontFace: t.font.body, color: t.text.secondary,
      align: 'center',
    });
  }
  if (data.notes) slide.addNotes(data.notes);
}

function renderSectionDivider(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  addSectionDivider(slide, data.title || '', t);
  addProgressBar(slide, idx + 1, total, t, { position: 'bottom', height: 0.05 });
  if (data.notes) slide.addNotes(data.notes);
}

function renderBullets(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);

  const bullets: any[] = (data.bullets || []).map((b: any) => {
    const txt = typeof b === 'string' ? b : (b.text || '');
    return {
      text: txt,
      options: {
        fontSize: 18, fontFace: t.font.body, color: t.text.primary,
        bullet: { code: '25B8' }, breakLine: true, paraSpaceAfter: 7,
      },
    };
  });

  if (bullets.length > 0) {
    slide.addText(bullets, {
      x: 0.7, y: 1.15, w: 8.6, h: 3.9, valign: 'top', lineSpacing: 24,
    });
  }

  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderQuote(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.accent };

  slide.addText('“', {
    x: 0.5, y: 0.3, w: 1, h: 1.2,
    fontSize: 80, fontFace: 'Georgia', color: 'ffffff', bold: true,
  });
  slide.addText(data.quote || '', {
    x: 1.3, y: 0.9, w: 7.5, h: 3.0,
    fontSize: 22, fontFace: t.font.body, color: 'ffffff',
    italic: true, lineSpacing: 34, valign: 'middle',
  });
  const attr = [data.author, data.role].filter(Boolean).join(', ');
  if (attr) {
    slide.addText(`— ${attr}`, {
      x: 1.3, y: 4.1, w: 7.5, h: 0.5,
      fontSize: 15, fontFace: t.font.body, color: 'e8e8ff',
    });
  }
  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderMetrics(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);
  addMetricsRow(slide, data.metrics || [], { x: 0.5, y: 1.3, w: 9, h: 2.8 }, t);
  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderFeatureGrid(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);
  addFeatureGrid(slide, data.features || [], { x: 0.5, y: 1.15, w: 9, h: 4.0 }, t);
  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderComparison(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);
  addComparisonTable(slide, data.columns || data, { x: 0.5, y: 1.15, w: 9, h: 3.9 }, t);
  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderTimeline(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);
  addTimeline(slide, data.milestones || [], { x: 0.5, y: 1.3, w: 9, h: 3.0 }, t);
  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderTwoColumn(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);

  const colW = 4.2;
  slide.addText(data.left || '', {
    x: 0.5, y: 1.15, w: colW, h: 3.9,
    fontSize: 16, fontFace: t.font.body, color: t.text.primary, valign: 'top', lineSpacing: 24,
  });
  slide.addShape('line', {
    x: 0.5 + colW + 0.2, y: 1.15, w: 0, h: 3.9, line: { color: t.text.secondary, width: 1 },
  });
  slide.addText(data.right || '', {
    x: 0.5 + colW + 0.5, y: 1.15, w: colW, h: 3.9,
    fontSize: 16, fontFace: t.font.body, color: t.text.primary, valign: 'top', lineSpacing: 24,
  });

  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

// ─── Backward-compat image layouts ───────────────────────────────────────────

function renderImages(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);

  const images: string[] = data.images || [];
  const captions: string[] = data.captions || [];
  const count = Math.min(images.length, 2);

  if (count === 1) {
    const cH = captions[0] ? 3.5 : 3.8;
    safeImage(slide, images[0], {
      x: 1.0, y: 1.15, w: 8.0, h: cH,
      sizing: { type: 'contain', w: 8.0, h: cH },
    });
    if (captions[0]) slide.addText(captions[0], {
      x: 1.0, y: 1.15 + cH + 0.05, w: 8.0, h: 0.3,
      fontSize: 11, fontFace: t.font.body, color: t.text.secondary, align: 'center', italic: true,
    });
  } else if (count === 2) {
    const cH = 3.5;
    const iW = 4.3;
    for (let i = 0; i < 2; i++) {
      const ix = 0.5 + i * (iW + 0.4);
      safeImage(slide, images[i], {
        x: ix, y: 1.15, w: iW, h: cH,
        sizing: { type: 'contain', w: iW, h: cH },
      });
      if (captions[i]) slide.addText(captions[i], {
        x: ix, y: 1.15 + cH + 0.05, w: iW, h: 0.3,
        fontSize: 11, fontFace: t.font.body, color: t.text.secondary, align: 'center', italic: true,
      });
    }
  }

  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderBulletsImage1(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);

  const imgPath = (data.images || [])[0] || '';
  const caption = (data.captions || [])[0] || '';
  const bullets: any[] = (data.bullets || []).map((b: any) => ({
    text: typeof b === 'string' ? b : (b.text || ''),
    options: {
      fontSize: 16, fontFace: t.font.body, color: t.text.primary,
      bullet: { code: '25B8' }, breakLine: true, paraSpaceAfter: 6,
    },
  }));

  // Bullets on left, image on right
  slide.addText(bullets, { x: 0.5, y: 1.15, w: 4.8, h: 3.9, valign: 'top', lineSpacing: 22 });
  const iH = caption ? 3.55 : 3.9;
  safeImage(slide, imgPath, {
    x: 5.5, y: 1.15, w: 4.0, h: iH,
    sizing: { type: 'contain', w: 4.0, h: iH },
  });
  if (caption) slide.addText(caption, {
    x: 5.5, y: 1.15 + iH + 0.05, w: 4.0, h: 0.3,
    fontSize: 11, fontFace: t.font.body, color: t.text.secondary, align: 'center', italic: true,
  });

  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderBulletsImage2(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);

  const images: string[] = data.images || [];
  const captions: string[] = data.captions || [];
  const bullets: any[] = (data.bullets || []).map((b: any) => ({
    text: typeof b === 'string' ? b : (b.text || ''),
    options: {
      fontSize: 16, fontFace: t.font.body, color: t.text.primary,
      bullet: { code: '25B8' }, breakLine: true, paraSpaceAfter: 5,
    },
  }));

  slide.addText(bullets, { x: 0.5, y: 1.15, w: 4.5, h: 3.9, valign: 'top', lineSpacing: 20 });
  const iW = 4.0;
  const slotH = 1.8;
  for (let i = 0; i < Math.min(images.length, 2); i++) {
    const iy = 1.15 + i * (slotH + 0.2);
    safeImage(slide, images[i], {
      x: 5.5, y: iy, w: iW, h: slotH,
      sizing: { type: 'contain', w: iW, h: slotH },
    });
    if (captions[i]) slide.addText(captions[i], {
      x: 5.5, y: iy + slotH + 0.02, w: iW, h: 0.2,
      fontSize: 10, fontFace: t.font.body, color: t.text.secondary, align: 'center', italic: true,
    });
  }

  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

function renderImageText(prs: any, data: any, t: SlideTheme, idx: number, total: number): void {
  const slide = prs.addSlide();
  slide.background = { color: t.bg.primary };
  addHeading(slide, data.title || '', t);

  const imgPath = (data.images || [])[0] || '';
  const caption = (data.captions || [])[0] || '';
  const iH = caption ? 3.5 : 3.9;

  safeImage(slide, imgPath, {
    x: 0.5, y: 1.15, w: 4.3, h: iH,
    sizing: { type: 'contain', w: 4.3, h: iH },
  });
  if (caption) slide.addText(caption, {
    x: 0.5, y: 1.15 + iH + 0.05, w: 4.3, h: 0.25,
    fontSize: 11, fontFace: t.font.body, color: t.text.secondary, align: 'center', italic: true,
  });

  slide.addText(data.text || '', {
    x: 5.1, y: 1.15, w: 4.4, h: 3.9,
    fontSize: 15, fontFace: t.font.body, color: t.text.primary, valign: 'top', lineSpacing: 22,
  });

  addSlideNumber(slide, idx + 1, total, t);
  if (data.notes) slide.addNotes(data.notes);
}

// ─── Router ───────────────────────────────────────────────────────────────────

type Renderer = (prs: any, data: any, t: SlideTheme, idx: number, total: number) => void;

const RENDERERS: Record<string, Renderer> = {
  cover:            renderCover,
  section_divider:  renderSectionDivider,
  bullets:          renderBullets,
  quote:            renderQuote,
  metrics:          renderMetrics,
  feature_grid:     renderFeatureGrid,
  comparison:       renderComparison,
  timeline:         renderTimeline,
  two_column:       renderTwoColumn,
  images:           renderImages,
  bullets_image1:   renderBulletsImage1,
  bullets_image2:   renderBulletsImage2,
  image_text:       renderImageText,
};

// ─── Main ─────────────────────────────────────────────────────────────────────

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error('Usage: npx tsx generate.ts <input.json> <output.pptx>');
  process.exit(1);
}

const spec = JSON.parse(readFileSync(inputPath, 'utf8'));
const slides: any[] = spec.slides || spec;  // support both {slides:[]} and plain []

const presetName = spec.theme || 'cleanCorporate';
theme = createTheme(PRESETS[presetName] ?? PRESETS['cleanCorporate']);

const prs = new pptxgen();
prs.layout = 'LAYOUT_16x9';

const total = slides.length;
for (let i = 0; i < slides.length; i++) {
  const slideData = slides[i];
  const layout = slideData.layout || 'bullets';
  const renderer = RENDERERS[layout] ?? renderBullets;
  renderer(prs, slideData, theme, i, total);
}

await prs.writeFile({ fileName: outputPath });
console.log(`OK: ${outputPath}`);
