import json
import pdfplumber
from pathlib import Path

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
_RESOLUTION = 150  # dpi for page rendering
_MIN_SIZE_PT = 30  # bỏ qua ảnh nhỏ hơn 30pt (icon, đường kẻ)


def _img_dir(file_path: str) -> Path:
    stem = Path(file_path).stem
    d = UPLOADS_DIR / f"{stem}_images"
    d.mkdir(exist_ok=True)
    return d


def _manifest_path(file_path: str) -> Path:
    return _img_dir(file_path) / "manifest.json"


def _load_manifest(file_path: str) -> list[dict]:
    mp = _manifest_path(file_path)
    if mp.exists():
        try:
            return json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_manifest(file_path: str, entries: list[dict]) -> None:
    _manifest_path(file_path).write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def extract_images(file_path: str, page_start: int, page_end: int) -> list[dict]:
    """
    Extract images từ [page_start, page_end] (1-indexed, inclusive).
    Bỏ qua các trang đã được extract trước đó.
    Trả về toàn bộ manifest sau khi extract xong.
    """
    manifest = _load_manifest(file_path)
    extracted_pages = {e["page"] for e in manifest}
    img_dir = _img_dir(file_path)
    scale = _RESOLUTION / 72  # PDF points → pixels

    new_count = 0

    with pdfplumber.open(file_path) as pdf:
        total = len(pdf.pages)
        p_start = max(1, page_start)
        p_end = min(total, page_end)

        for page_num in range(p_start, p_end + 1):
            if page_num in extracted_pages:
                continue

            page = pdf.pages[page_num - 1]
            images = page.images
            if not images:
                continue

            # Render trang thành ảnh PIL để crop
            try:
                page_img = page.to_image(resolution=_RESOLUTION)
                pil = page_img.original
            except Exception:
                continue

            pw, ph = pil.size
            page_h_pt = page.height  # chiều cao trang tính bằng points

            for idx, img_info in enumerate(images):
                x0 = img_info.get("x0", 0)
                y0 = img_info.get("y0", 0)
                x1 = img_info.get("x1", 0)
                y1 = img_info.get("y1", 0)
                w_pt = x1 - x0
                h_pt = y1 - y0

                if w_pt < _MIN_SIZE_PT or h_pt < _MIN_SIZE_PT:
                    continue

                # PDF dùng toạ độ góc dưới-trái → đổi sang PIL (góc trên-trái)
                cx0 = max(0, min(int(x0 * scale), pw))
                cy0 = max(0, min(int((page_h_pt - y1) * scale), ph))
                cx1 = max(0, min(int(x1 * scale), pw))
                cy1 = max(0, min(int((page_h_pt - y0) * scale), ph))

                if cx1 <= cx0 or cy1 <= cy0:
                    continue

                cropped = pil.crop((cx0, cy0, cx1, cy1))
                fname = f"page{page_num:03d}_img{idx + 1:02d}.png"
                cropped.save(str(img_dir / fname), "PNG")

                manifest.append({
                    "filename": fname,
                    "path": str(img_dir / fname),
                    "page": page_num,
                    "index": idx + 1,
                    "x0": round(x0, 1),
                    "y0": round(y0, 1),
                    "x1": round(x1, 1),
                    "y1": round(y1, 1),
                    "width_pt": round(w_pt, 1),
                    "height_pt": round(h_pt, 1),
                })
                new_count += 1

    if new_count > 0:
        _save_manifest(file_path, manifest)

    return manifest


def annotate_images(file_path: str, annotations: list[dict]) -> int:
    """
    Cập nhật trường 'about' cho các ảnh trong manifest.
    annotations: [{"filename": "page005_img01.png", "about": "mô tả ảnh"}]
    Trả về số lượng ảnh đã cập nhật.
    """
    manifest = _load_manifest(file_path)
    if not manifest:
        return 0

    index = {e["filename"]: e for e in manifest}
    updated = 0
    for ann in annotations:
        fname = ann.get("filename", "")
        about = ann.get("about", "")
        if fname in index and about:
            index[fname]["about"] = about
            updated += 1

    if updated:
        _save_manifest(file_path, list(index.values()))
    return updated


def get_manifest(file_path: str) -> list[dict]:
    return _load_manifest(file_path)
