---
name: slide-content
description: Guidelines for the analyst to prepare slide outline content when a presentation is requested
---

## Mandatory Task

When this skill is activated, the "slides" field in the output JSON MUST be filled — this is the primary output of the request:
- Read the document thoroughly to gather enough information for each slide
- Extract images from PDFs if the document contains embedded figures (prioritize pages with images)
- Build the "slides" field before finishing — do NOT return output with "slides" still as []

## The "slides" Field in Output

"slides" is an array of slides in order. Each element follows one of the 6 layout schemas below:

Layout cover — title slide, always the first slide:
{"layout": "cover", "title": "Report Title", "subtitle": "Author / Date / Course"}

Layout bullets — bullet list, most commonly used:
Each bullet CAN be a plain string, or an object {"text": "...", "sub": "..."} for additional explanation.
{"layout": "bullets", "number": 1, "title": "Key Results for 2024", "bullets": [
  {"text": "Q4 +340% vs Q3", "sub": "Highest growth ever recorded"},
  {"text": "Product A accounts for 67% of revenue", "sub": "Up from 45% year-over-year"},
  "Northern region leads"
]}

Layout bullets_image1 — bullets + 1 image (position auto-adjusted by image orientation):
{"layout": "bullets_image1", "number": 2, "title": "System Architecture", "bullets": ["3-step processing pipeline", "Automatic entity linking"], "images": ["/absolute/path/image.png"], "captions": ["Figure 5: NLP pipeline architecture diagram"]}

Layout bullets_image2 — bullets + 2 images (position auto-adjusted):
{"layout": "bullets_image2", "number": 3, "title": "Model Comparison", "bullets": ["PhoBERT F1 = 0.724", "Baseline F1 = 0.61"], "images": ["/path/img1.png", "/path/img2.png"], "captions": ["Figure 8: Accuracy per epoch", "Figure 9: Confusion matrix"]}

Layout images — 1 or 2 images, no bullets:
{"layout": "images", "number": 4, "title": "Sentiment Correlation Chart", "images": ["/path/chart.png"], "captions": ["Figure 12: Lag 0-5 day correlation"]}

Layout image_text — image + paragraph (position auto-adjusted):
{"layout": "image_text", "number": 5, "title": "Event Analysis", "images": ["/path/event.png"], "captions": ["Figure 15: Cumulative return after event"], "text": "Stock prices reacted strongly within 1 day of major events, average amplitude ±3.2%."}

## Bullet Writing Rules

- 3-6 bullets per content slide (except cover and Q&A slides)
- Each bullet text: 5-15 words
- Start with a specific figure or action word (not "The", "About", "Regarding")
- Slide title = conclusion or key message, not a topic label

Sub-bullets ("sub" field):
- Use for slides WITHOUT images (layout "bullets") to elaborate on the main bullet
- Each sub: max 15 words, concise and specific
- Slides with images (bullets_image1, bullets_image2) should NOT use sub — the image already illustrates

## Image Rules

- Only use image layouts if you have real image paths from pdf_extract_images
- Use the "path" field from the manifest — absolute path to the PNG file
- Prefer images that have an "about" annotation
- Do not place fake paths in images if extraction hasn't been done
- Image position (horizontal/vertical, top/bottom, left/right) is handled automatically by the renderer
- "captions" field: array of strings parallel to "images" — one caption per image in order
- Caption from manifest "about" field or from caption text near the image in the PDF (e.g. "Figure X: ...")
- If no caption is available, omit "captions" or leave as []

## Workflow When Creating Slides from a PDF

Step 1: Read document content — use pdf_rag_search or pdf_summarize_pages to understand the structure.
Step 2: Read key sections in detail — use pdf_read_pages for pages with data, tables, results.
Step 3 (if document has images): Call pdf_extract_images for pages with relevant figures.
Step 4 (if images exist): Call pdf_read_pages for those pages, then annotate with pdf_annotate_images.
Step 5: Build the "slides" outline based on content read.

## Standard Deck Structure

- Slide 1: layout "cover" — title + author/date
- Slide 2: layout "bullets" — agenda (3-5 major sections to cover)
- Slides 3 to N-1: main content, one key finding or major topic per slide
- Slide N-1: layout "bullets" — conclusion + recommended actions
- Slide N: layout "bullets", bullets=[] — "Q&A"

## Slide Count by Document Length

Short report (under 15 pages): 6-8 slides
Medium report (15-40 pages): 10-14 slides
Long report (over 40 pages): 14-20 slides
If user requests "detailed" or "comprehensive": no cap; ~1-3 slides per major chapter/section
