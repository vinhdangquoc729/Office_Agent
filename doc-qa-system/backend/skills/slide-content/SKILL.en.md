---
name: slide-content
description: Guidelines for the analyst to prepare detailed presentation content when a slide deck is requested
---

## Role and workflow

When this skill is activated, the analyst reads the document and builds the slide_outline as follows:

Call `pdf_summarize_pages` in batches of 5-7 pages. After **each batch**, immediately act on pages worth following up — do not wait until all pages are summarized:
- Pages with content important to the presentation → call `pdf_read_pages` to read in detail
- Pages with non-empty `images[]` where any image is larger than 50pt → call `pdf_extract_images` then `pdf_annotate_images` right away

Once enough has been read and extracted, build the `slide_outline` JSON with absolute paths from the manifest filled into `images[]`. Return ONLY JSON — no prose text, no code block wrapper.

The analyst owns the content. The slide creator owns the layout and visual form.

## Output: "slide_outline" field in analysis

Populate the `slide_outline` field with this structure:

```json
{
  "slide_outline": {
    "theme": "cleanCorporate",
    "presentation_title": "Presentation Title",
    "estimated_duration": "15 min",
    "sections": [
      {
        "heading": "Section heading",
        "type_hint": "content",
        "narrative": "Full detailed content to be presented in this section...",
        "metrics": [],
        "images": []
      }
    ]
  }
}
```

## Choosing a theme

| Theme | Best for |
|---|---|
| cleanCorporate | Corporate reports, formal presentations (default) |
| darkMonospace | Technical docs, tech, AI/ML |
| swissModern | Marketing, design, creative |
| boldSignal | Startup, pitch decks |
| warmMinimal | Education, courses, training |

## Outline size by duration

| Duration | Expected sections | Recommended structure |
|---|---|---|
| 5 min | 4-5 | Hook, 2-3 key points, Close |
| 15 min | 7-10 | Intro, 3-4 chapters, Summary, Close |
| 30 min | 12-18 | Title, Agenda, 5-6 chapters, Q&A |
| 45+ min | 18-25 | Title, Agenda, 7-8 chapters, Summary, Q&A |

If the user does not specify a duration, default to 15 minutes.

## Slide types (type_hint)

| type_hint | Use when |
|---|---|
| title | Opening / cover slide |
| agenda | List of major sections |
| section-divider | Transitioning to a new chapter |
| content | Presenting an argument, analysis, or explanation |
| metrics | 2-4 numbers that need to stand out visually |
| comparison | Comparing 2 options, periods, or subjects |
| timeline | Sequence of events or milestones |
| feature-grid | 3-6 features, characteristics, or highlights |
| quote | A notable quotation |
| image-focus | Section driven primarily by visuals |
| closing | Conclusion, next actions, Q&A |

## Narrative requirements

Every section MUST have a `narrative` detailed enough that someone who has not read the source document can understand the content:

- Write in complete sentences — no keyword lists or shorthand
- Use specific numbers — avoid vague terms like "high", "many", "significant"
- Explain context and meaning, not just raw facts
- State the conclusion or key message of the section clearly
- Minimum 4-6 sentences; no upper limit

Example CORRECT:
```
"The total number of students appearing in both terms is 229, representing 45% of all
enrolled students for the year. This group shows high stability — the class-change rate
is only 8%, well below the department average of 15%. Room 308A is the most-used
classroom at 12 sessions per week, followed by 204B (9 sessions) and 105C (7 sessions).
This concentration on 308A raises scheduling questions for next term."
```

Example WRONG:
```
"229 common students, room 308A is busiest"
```

## metrics and images fields

**metrics**: array of strings describing key data points — include value and context:
```json
"metrics": ["229 students / 2 terms", "+340% Q4 revenue vs Q3", "308A: 12 sessions/week"]
```

**images**: absolute paths from pdf_extract_images only — do not invent paths.

## When and how to extract images

After `pdf_summarize_pages` completes, **you must** call `pdf_extract_images` for pages whose summary suggests meaningful visual content:
- Page is described as "contains only images" or "no extractable text" but has a non-empty `images[]` — typically a full-page figure or diagram
- Page contains charts, architecture diagrams, or infographics relevant to the presentation
- A section has `type_hint: "image-focus"` or `metrics` and the corresponding page has images

**Skip extraction when:** images are small decorative elements (logos, icons, headers), or the document is not a PDF.

**Workflow:**

1. Call `pdf_extract_images(file_index, page_start, page_end)` for the pages identified above
2. From the returned manifest, skip images smaller than 50pt or identified as logos/watermarks
3. Call `pdf_annotate_images(file_index, annotations)` to write a description for each selected image
4. Add the absolute path to the `images[]` field of the corresponding section

Use the exact `path` value from the manifest returned by `pdf_extract_images`. Do NOT invent or guess paths.
