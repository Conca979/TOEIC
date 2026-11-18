from __future__ import annotations

import argparse
import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader

GRAPHIC_Q_RE = re.compile(r"(\d+)\.\s*Look at the graphic", re.IGNORECASE)
LOOK_AT_GRAPHIC_RE = re.compile(r"Look at the graphic", re.IGNORECASE)


@dataclass
class ExtractedImage:
    test: int
    part: int
    questions: str
    page: int
    bbox: list[int]
    width: int
    height: int
    file: str


def extract_page_scan(page) -> Image.Image:
    """Return the main full-page grayscale scan from a PDF page, skipping watermark overlays."""
    resources = page.get("/Resources")
    if resources:
        xobjects = resources.get("/XObject")
        if xobjects:
            best_obj = None
            best_area = 0
            for obj_ref in xobjects.get_object().values():
                obj = obj_ref.get_object()
                if obj.get("/Subtype") == "/Image":
                    area = int(obj.get("/Width", 0)) * int(obj.get("/Height", 0))
                    if area > best_area:
                        best_area = area
                        best_obj = obj
            if best_obj is not None:
                return Image.open(io.BytesIO(best_obj.get_data())).convert("L")

    best_img = max(page.images, key=lambda im: len(im.data))
    return Image.open(io.BytesIO(best_img.data)).convert("L")


def _find_runs(mask: np.ndarray, min_len: int, max_gap: int = 0) -> list[tuple[int, int]]:
    """Find contiguous True runs in a 1D boolean array, bridging gaps up to max_gap."""
    if max_gap > 0 and mask.any():
        padded = mask.copy()
        idx = np.flatnonzero(mask)
        for a, b in zip(idx[:-1], idx[1:]):
            if 1 < (b - a) <= max_gap + 1:
                padded[a:b] = True
        mask = padded

    diff = np.diff(mask.astype(np.int8), prepend=0, append=0)
    starts = np.flatnonzero(diff == 1)
    ends = np.flatnonzero(diff == -1) - 1
    return [(int(s), int(e)) for s, e in zip(starts, ends) if (e - s + 1) >= min_len]


def detect_part1_photos(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Detect Part 1 rectangular photo blocks on a scanned page."""
    h, w = gray.shape
    x_min_body, x_max_body = 240, min(1130, w - 50)
    y_min_body, y_max_body = 40, min(1550, h - 80)

    body = gray[y_min_body:y_max_body, x_min_body:x_max_body]
    row_dark_frac = (body < 240).mean(axis=1)
    y_bands = _find_runs(row_dark_frac > 0.04, min_len=240, max_gap=10)

    boxes: list[tuple[int, int, int, int]] = []
    for yt_rel, yb_rel in y_bands:
        yt = y_min_body + yt_rel
        yb = y_min_body + yb_rel
        band = gray[yt : yb + 1, x_min_body:x_max_body]
        col_dark_frac = (band < 240).mean(axis=0)
        x_runs = _find_runs(col_dark_frac > 0.04, min_len=350, max_gap=12)
        if not x_runs:
            continue
        xl = x_min_body + min(s for s, _ in x_runs)
        xr = x_min_body + max(e for _, e in x_runs)

        crop = gray[yt : yb + 1, xl : xr + 1]
        ys, xs = np.where(crop < 245)
        if len(ys) == 0:
            continue
        boxes.append((
            int(xl + xs.min()),
            int(yt + ys.min()),
            int(xl + xs.max() + 1),
            int(yt + ys.max() + 1),
        ))
    return boxes


def _merge_horizontal_lines(lines: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Merge horizontal line segments on rows within 4px that overlap by >= 120px."""
    if not lines:
        return []
    lines.sort()
    merged: list[list[int]] = []
    for y, x1, x2 in lines:
        placed = False
        for m in reversed(merged):
            if y - m[1] > 4:
                break
            overlap = min(x2, m[3]) - max(x1, m[2])
            if overlap >= 120:
                m[1] = y
                m[2] = min(m[2], x1)
                m[3] = max(m[3], x2)
                placed = True
                break
        if not placed:
            merged.append([y, y, x1, x2])
    return [((y0 + y1) // 2, x1, x2) for y0, y1, x1, x2 in merged]


def detect_boxed_graphics(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Detect outermost rectangular bordered graphics (tables, charts, maps) on Part 3/4 pages."""
    h, w = gray.shape
    x_min_body, x_max_body = 40, min(1150, w - 50)
    y_min_body, y_max_body = 40, min(1550, h - 80)

    dark = gray < 205
    raw_h_lines: list[tuple[int, int, int]] = []
    for y in range(y_min_body + 1, y_max_body - 1):
        band = dark[y - 1 : y + 2, x_min_body:x_max_body].any(axis=0)
        for s, e in _find_runs(band, min_len=240, max_gap=6):
            raw_h_lines.append((y, x_min_body + s, x_min_body + e))

    h_lines = _merge_horizontal_lines(raw_h_lines)

    candidates: list[tuple[int, int, int, int]] = []
    for i, (yt, xt1, xt2) in enumerate(h_lines):
        for yb, xb1, xb2 in h_lines[i + 1 :]:
            height = yb - yt
            if height < 60:
                continue
            # Allow larger top-left offset for corner badges or indented top borders
            if abs(xt1 - xb1) > 90 or abs(xt2 - xb2) > 25:
                continue
            xl = min(xt1, xb1)
            xr = max(xt2, xb2)
            if xr - xl < 260:
                continue

            # Check vertical borders anchored on bottom edge (or top edge if right is slightly indented)
            left_x = xb1 if abs(xt1 - xb1) > 8 else xl
            right_x = xb2 if abs(xt2 - xb2) <= 10 else xr
            left_strip = dark[yt : yb + 1, max(0, left_x - 6) : left_x + 7].any(axis=1)
            right_strip = dark[yt : yb + 1, max(0, right_x - 6) : right_x + 7].any(axis=1)
            top_right_conn = dark[yt + 3 : min(yb, yt + 24), max(0, right_x - 6) : right_x + 7].any(axis=1)
            bot_left_conn = dark[max(yt, yb - 24) : max(yt + 1, yb - 2), max(0, left_x - 6) : left_x + 7].any(axis=1)
            if (
                left_strip.mean() >= 0.72
                and right_strip.mean() >= 0.78
                and top_right_conn.mean() >= 0.65
                and bot_left_conn.mean() >= 0.65
            ):
                candidates.append((left_x, yt, right_x + 1, yb + 1))

    # Keep only outermost rectangles (discard inner table cells/sub-boxes)
    outermost: list[tuple[int, int, int, int]] = []
    for idx, (x1, y1, x2, y2) in enumerate(candidates):
        area = (x2 - x1) * (y2 - y1)
        contained = False
        for jdx, (ox1, oy1, ox2, oy2) in enumerate(candidates):
            if idx == jdx:
                continue
            o_area = (ox2 - ox1) * (oy2 - oy1)
            if o_area <= area:
                continue
            if ox1 - 10 <= x1 and oy1 - 10 <= y1 and ox2 + 10 >= x2 and oy2 + 10 >= y2:
                contained = True
                break
        if not contained:
            outermost.append((x1, y1, x2, y2))

    # Deduplicate near-identical boxes
    deduped: list[tuple[int, int, int, int]] = []
    for box in sorted(outermost, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True):
        if any(
            abs(box[0] - d[0]) <= 15
            and abs(box[1] - d[1]) <= 15
            and abs(box[2] - d[2]) <= 15
            and abs(box[3] - d[3]) <= 15
            for d in deduped
        ):
            continue
        deduped.append(box)

    mid_x = w / 2
    deduped.sort(key=lambda b: (0 if (b[0] + b[2]) / 2 < mid_x else 1, b[1]))
    return deduped


def _boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return False
    inter = (ix2 - ix1) * (iy2 - iy1)
    min_area = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return inter > 0.1 * min_area


def _detect_column_band_fallback(
    gray: np.ndarray,
    col_x_range: tuple[int, int],
    y_search_range: tuple[int, int],
) -> tuple[int, int, int, int] | None:
    """Fallback detector for lighter/partial-border graphic blocks inside a column band."""
    x0, x1 = col_x_range
    y0, y1 = y_search_range
    sub = gray[y0:y1, x0:x1]
    dark = sub < 232
    row_has_ink = dark.sum(axis=1) >= 12
    # Graphics have much taller contiguous ink blocks (bridging text gaps inside boxes up to 32px)
    runs = _find_runs(row_has_ink, min_len=95, max_gap=32)
    if not runs:
        return None
    # Pick widest/tallest candidate block near top of band
    best_box = None
    best_score = -1
    for rs, re_ in runs:
        block = dark[rs : re_ + 1, :]
        col_ink = block.sum(axis=0) >= 3
        xs = np.flatnonzero(col_ink)
        if len(xs) == 0:
            continue
        bx1 = x0 + int(xs.min())
        bx2 = x0 + int(xs.max()) + 1
        by1 = y0 + rs
        by2 = y0 + re_ + 1
        bw = bx2 - bx1
        bh = by2 - by1
        if bw < 260 or bh < 95:
            continue
        score = bw * bh
        if score > best_score:
            best_score = score
            best_box = (bx1, by1, bx2, by2)
    return best_box


def _question_group_label(q_num: int, part: int) -> str:
    base = 32 if part == 3 else 71
    start = base + ((q_num - base) // 3) * 3
    return f"q{start:02d}-{start + 2:02d}"


def _extract_graphic_groups_from_page(page, part: int) -> list[str]:
    """Find ordered unique graphic question groups (e.g. 'q65-67') on a Listening page."""
    text = page.extract_text() or ""
    q_nums = [int(m.group(1)) for m in GRAPHIC_Q_RE.finditer(text)]

    # Handle OCR line-breaks where number appears several lines earlier (e.g., "94." then options/text then "Look at the graphic")
    if not q_nums and LOOK_AT_GRAPHIC_RE.search(text):
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if LOOK_AT_GRAPHIC_RE.search(line):
                window = " ".join(lines[max(0, idx - 25) : idx + 1])
                nums = [int(n) for n in re.findall(r"\b(\d{2,3})\.", window)]
                valid_nums = [n for n in nums if (32 <= n <= 70 if part == 3 else 71 <= n <= 100)]
                if valid_nums:
                    q_nums.append(valid_nums[-1])

    groups: list[str] = []
    for q in q_nums:
        label = _question_group_label(q, part)
        if label not in groups:
            groups.append(label)
    return groups


def _find_question_y_cutoff(page, q_start: int, default_y: int, page_height: int) -> int:
    """Estimate pixel Y coordinate where a question number appears, using PDF text coordinates."""
    found_y: list[float] = []

    def visitor(text, cm, tm, font_dict, font_size):
        if re.search(rf"\b{q_start}\.", text):
            found_y.append(tm[5])

    try:
        page.extract_text(visitor_text=visitor)
    except Exception:
        return default_y

    if not found_y:
        return default_y

    pdf_h = float(page.mediabox.height)
    # PDF origin is bottom-left; image origin is top-left
    img_y = int((1.0 - (found_y[0] / pdf_h)) * page_height)
    return max(150, min(page_height - 100, img_y - 12))


def extract_test_images(
    reader: PdfReader,
    test_id: int,
    listening_range: tuple[int, int],
    part1_pages: list[tuple[int, list[int]]],
    out_dir: Path,
    pages_dir: Path | None = None,
) -> list[ExtractedImage]:
    """Extract Part 1, Part 3, and Part 4 images for a single Listening test."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if pages_dir is not None:
        pages_dir.mkdir(parents=True, exist_ok=True)

    records: list[ExtractedImage] = []
    pad = 4

    # Part 1 photos
    for page_num, q_nums in part1_pages:
        scan = extract_page_scan(reader.pages[page_num - 1])
        gray = np.asarray(scan)
        boxes = detect_part1_photos(gray)
        if len(boxes) != len(q_nums):
            raise RuntimeError(
                f"Test {test_id} p{page_num}: expected {len(q_nums)} Part 1 photos, found {len(boxes)}"
            )
        for q_num, (x1, y1, x2, y2) in zip(q_nums, boxes):
            crop_box = (
                max(0, x1 - pad),
                max(0, y1 - pad),
                min(scan.width, x2 + pad),
                min(scan.height, y2 + pad),
            )
            cropped = scan.crop(crop_box)
            filename = f"part1_q{q_num:02d}.jpg"
            cropped.save(out_dir / filename, quality=95)
            records.append(
                ExtractedImage(
                    test=test_id,
                    part=1,
                    questions=f"q{q_num:02d}",
                    page=page_num,
                    bbox=list(crop_box),
                    width=cropped.width,
                    height=cropped.height,
                    file=filename,
                )
            )

    # Part 3 and Part 4 integrated graphics
    start_p, end_p = listening_range
    p1_page_nums = {p for p, _ in part1_pages}
    part = 3
    for page_num in range(start_p + 2, end_p + 1):
        if page_num in p1_page_nums:
            continue
        page = reader.pages[page_num - 1]
        text = page.extract_text() or ""
        if "PART 4" in text or re.search(r"\b(?:7[1-9]|8\d|9\d|100)\.", text):
            part = 4

        groups = _extract_graphic_groups_from_page(page, part)
        if not groups:
            continue

        scan = extract_page_scan(page)
        if pages_dir is not None:
            scan.save(pages_dir / f"listening_p{page_num:03d}.jpg", quality=92)

        gray = np.asarray(scan)
        boxes = detect_boxed_graphics(gray)

        # Column-band fallback if strict border detection found fewer boxes than expected
        if len(boxes) < len(groups):
            matched_boxes: list[tuple[int, int, int, int]] = list(boxes)
            mid_x = scan.width // 2
            for g_idx, label in enumerate(groups):
                q_start = int(label[1:3])
                # Expected column: q62-64 and q92-94 are middle/top of right column;
                # pairs (q65-67, q68-70) and (q95-97, q98-100) are left then right column
                if len(groups) == 2:
                    col_range = (60, mid_x - 10) if g_idx == 0 else (mid_x - 5, min(1145, scan.width - 50))
                    y_cut = _find_question_y_cutoff(page, q_start, 540, scan.height)
                    y_range = (70, y_cut)
                else:
                    col_range = (mid_x - 5, min(1145, scan.width - 50))
                    y_cut = _find_question_y_cutoff(page, q_start, 950, scan.height)
                    y_range = (max(70, y_cut - 550), y_cut)

                # Check if an already detected box lives in this column band
                already = [
                    b
                    for b in matched_boxes
                    if col_range[0] <= (b[0] + b[2]) / 2 <= col_range[1]
                    and y_range[0] - 40 <= (b[1] + b[3]) / 2 <= y_range[1] + 40
                ]
                if not already:
                    fb = _detect_column_band_fallback(gray, col_range, y_range)
                    if fb is not None and not any(_boxes_overlap(fb, b) for b in matched_boxes):
                        matched_boxes.append(fb)

            matched_boxes.sort(key=lambda b: (0 if (b[0] + b[2]) / 2 < mid_x else 1, b[1]))
            boxes = matched_boxes

        if len(boxes) != len(groups):
            raise RuntimeError(
                f"Test {test_id} p{page_num}: found {len(boxes)} boxes {boxes} "
                f"but {len(groups)} graphic question groups ({groups})"
            )

        for label, (x1, y1, x2, y2) in zip(groups, boxes):
            crop_box = (
                max(0, x1 - pad),
                max(0, y1 - pad),
                min(scan.width, x2 + pad),
                min(scan.height, y2 + pad),
            )
            cropped = scan.crop(crop_box)
            filename = f"part{part}_{label}.jpg"
            cropped.save(out_dir / filename, quality=95)
            records.append(
                ExtractedImage(
                    test=test_id,
                    part=part,
                    questions=label,
                    page=page_num,
                    bbox=list(crop_box),
                    width=cropped.width,
                    height=cropped.height,
                    file=filename,
                )
            )

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps([asdict(r) for r in records], indent=2), encoding="utf-8")
    return records


def extract_test1_prototype(pdf_path: Path, out_dir: Path) -> list[ExtractedImage]:
    reader = PdfReader(str(pdf_path))
    return extract_test_images(
        reader=reader,
        test_id=1,
        listening_range=(1, 13),
        part1_pages=[(3, [1, 2]), (4, [3, 4]), (5, [5, 6])],
        out_dir=out_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Listening Test 1 images (Part 1, 3, 4).")
    parser.add_argument("--pdf", type=Path, default=Path("Hacker 3/HAKER 3 LISTENING.pdf"))
    parser.add_argument("--out", type=Path, default=Path("extracted/test-01/images"))
    args = parser.parse_args()

    records = extract_test1_prototype(args.pdf, args.out)
    print(f"Extracted {len(records)} images to {args.out}:")
    for r in records:
        print(f"  p{r.page:02d} Part {r.part} ({r.questions}): {r.file} [{r.width}x{r.height}]")


if __name__ == "__main__":
    main()
