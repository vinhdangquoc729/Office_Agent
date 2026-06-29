import pdfplumber

_RESOLUTION = 150  # dpi — phải khớp với image_extractor để tọa độ nhất quán
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['vi', 'en'], gpu=False)
    return _reader


def ocr_page(file_path: str, page_number: int) -> list[dict]:
    """
    OCR toàn bộ trang PDF, trả về list các text block với tọa độ PDF points.
    Mỗi phần tử: {text, confidence, x0, y0, x1, y1} (pt, góc trên-trái hệ PDF).
    """
    with pdfplumber.open(file_path) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            return []
        page = pdf.pages[page_number - 1]
        page_h_pt = page.height
        pil = page.to_image(resolution=_RESOLUTION).original

    scale = _RESOLUTION / 72  # pixels per pt

    import numpy as np
    reader = _get_reader()
    results = reader.readtext(np.array(pil))

    blocks = []
    for bbox, text, conf in results:
        if not text.strip():
            continue
        # bbox: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] pixel coords (top-left origin)
        px_xs = [p[0] for p in bbox]
        px_ys = [p[1] for p in bbox]
        px_x0, px_x1 = min(px_xs), max(px_xs)
        px_y0, px_y1 = min(px_ys), max(px_ys)

        # Convert pixel → pt, flip Y (PDF: origin bottom-left)
        pt_x0 = px_x0 / scale
        pt_x1 = px_x1 / scale
        pt_y0 = page_h_pt - px_y1 / scale
        pt_y1 = page_h_pt - px_y0 / scale

        blocks.append({
            "text": text.strip(),
            "confidence": round(conf, 3),
            "x0": round(pt_x0, 1),
            "y0": round(pt_y0, 1),
            "x1": round(pt_x1, 1),
            "y1": round(pt_y1, 1),
        })

    return blocks
