---
name: pdf-extraction
description: Guidelines for handling different PDF types and using page-level PDF reading tools
---

## Available Tools

All PDF tools accept file_index (integer, index in the document list) instead of file_path.
The document list and corresponding indices are provided at the start of the context.

pdf_get_page_count(file_index)
- Returns: integer total page count
- Use when you don't know the document length (file_content already has total_pages from metadata; use this to confirm)

pdf_summarize_pages(file_index, page_start, page_end)
- Asks the helper to summarize each page in the range [page_start, page_end] (1-indexed, inclusive)
- Each page returns: page_number, summary, images (coordinates)
- Call with at most 5-7 pages at a time — the helper can't handle more reliably
- Use to: get an overview before deciding which pages to read in detail

pdf_read_pages(file_index, page_start, page_end)
- Returns: list of pages, each with text, tables, images (position + size), annots
- Use when: the request asks about specific content from a known page
- Prefer this over summarize when you need accurate data (names, figures, tables)

pdf_read_pages_detailed(file_index, page_start, page_end)
- Like pdf_read_pages but adds chars (font, size, color, coordinates), lines, rects
- Only use when you need exact element positions (detect headings, analyze layout)
- Heavier — use sparingly

pdf_extract_images(file_index, page_start, page_end)
- Extracts images from the specified page range, saves to disk, returns a JSON manifest
- Pages already extracted are skipped (no repeat work)
- Manifest includes: filename, path, page, index, x0/y0/x1/y1, width_pt/height_pt
- Use when: images need to go into slides, or user asks about images in the document

pdf_annotate_images(file_index, annotations)
- Writes the "about" (description) field for each image in the manifest
- annotations: [{"filename": "page005_img01.png", "about": "Q1-Q4 2024 revenue chart"}]
- Call AFTER reading the page text to infer image content

pdf_ocr_page(file_index, page_number)
- OCR a PDF page, returns plain text joined top-to-bottom
- Use when pdf_read_pages shows _ocr_hint or sparse text on a page that has images
- Slower than pdf_read_pages — only use when necessary

pdf_ocr_page_detailed(file_index, page_number)
- Like pdf_ocr_page but returns full block list: {text, confidence, x0, y0, x1, y1}
- Use when you need exact text positions (captions, layout, specific regions)

run_code(code)
- Runs Python (pandas, numpy) for computation and statistics
- Use when you need to process already-read data

pdf_rag_search(file_index, query)
- Semantic search across the entire document; returns the most relevant passages with page numbers
- First call indexes the whole document (slower); subsequent calls are fast
- Use when: the document is long and you don't know which page contains the information

## Reading Strategy

If the request asks about a specific page (e.g. "who is on page 69"):
- Call pdf_read_pages directly for that exact page
- If the page has _ocr_hint or sparse text while images[] is non-empty → MUST call pdf_ocr_page to read image content
- If text is completely empty → MUST call pdf_ocr_page
- Only use pdf_ocr_page_detailed when exact coordinates are needed (layout, caption position)

If you need to find information but don't know which page (document > 30 pages):
- Use pdf_rag_search(file_index, query) to locate the page
- Then call pdf_read_pages on the found pages for full content

If the document is short (< 30 pages) and full analysis is needed:
- Use pdf_summarize_pages in chunks of 5-7 pages
- Only read details for chunks containing important information

## Image Workflow

When you need to understand or use images in the document:

Step 1: Call pdf_extract_images to extract images from relevant pages.
Step 2: Call pdf_read_pages for those same pages to get the text.
Step 3: For each image in the manifest, use position (x0/y0/x1/y1) to identify nearby text (caption, title, note). Text with y close to the image's y1 is typically a caption below.
Step 4: Call pdf_annotate_images to write the inferred description into the manifest.
Step 5: Use "path" from the manifest to pass into a slide layout.

## PDF Type Recognition

Text-based PDF: text extraction is accurate; tables and lists are recognized.
Scanned PDF: text is empty or sparse, cannot be extracted — warn the user.
Mixed: note each scanned page individually.

## Tables Spanning Multiple Pages

Reassemble based on matching column headers. If reassembly is not possible, present each section separately and note "continued from page X".

## Image Notes

When a page's images[] is non-empty: note "[Image on page X at (x0,y0)-(x1,y1)]".
If an image has an adjacent caption, quote the caption.
