from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from toeic.extract_images import extract_test_images


@dataclass(frozen=True)
class TestSpec:
    test_id: int
    listening_range: tuple[int, int]
    part1_pages: list[tuple[int, list[int]]]
    reading_range: tuple[int, int]


TEST_SPECS: list[TestSpec] = [
    TestSpec(1, (1, 13), [(3, [1, 2]), (4, [3, 4]), (5, [5, 6])], (1, 29)),
    TestSpec(2, (14, 26), [(16, [1, 2]), (17, [3, 4]), (18, [5, 6])], (30, 58)),
    TestSpec(3, (27, 39), [(29, [1, 2]), (30, [3, 4]), (31, [5, 6])], (59, 87)),
    TestSpec(4, (40, 48), [(41, [3, 4]), (42, [5, 6])], (88, 116)),
    TestSpec(5, (49, 60), [(50, [1, 2]), (51, [3, 4]), (52, [5, 6])], (117, 145)),
    TestSpec(6, (61, 73), [(63, [1, 2]), (64, [3, 4]), (65, [5, 6])], (146, 174)),
    TestSpec(7, (74, 86), [(76, [1, 2]), (77, [3, 4]), (78, [5, 6])], (175, 203)),
    TestSpec(8, (87, 99), [(89, [1, 2]), (90, [3, 4]), (91, [5, 6])], (204, 232)),
    TestSpec(9, (100, 112), [(102, [1, 2]), (103, [3, 4]), (104, [5, 6])], (233, 261)),
    TestSpec(10, (113, 125), [(115, [1, 2]), (116, [3, 4]), (117, [5, 6])], (262, 290)),
]


def _write_pdf_slice(reader: PdfReader, page_range: tuple[int, int], out_pdf: Path) -> None:
    writer = PdfWriter()
    start_p, end_p = page_range
    for page_num in range(start_p, end_p + 1):
        writer.add_page(reader.pages[page_num - 1])
    with out_pdf.open("wb") as f:
        writer.write(f)


def _write_ocr_dump(reader: PdfReader, page_range: tuple[int, int], out_txt: Path) -> None:
    chunks: list[str] = []
    start_p, end_p = page_range
    for idx, page_num in enumerate(range(start_p, end_p + 1), start=1):
        text = reader.pages[page_num - 1].extract_text() or ""
        chunks.append(f"=== LOCAL PAGE {idx} (SOURCE PAGE {page_num}) ===\n{text.strip()}")
    out_txt.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")


def prepare_all_tests(
    listening_pdf: Path = Path("Hacker 3/HAKER 3 LISTENING.pdf"),
    reading_pdf: Path = Path("Hacker 3/HACKER 3 READING.pdf"),
    out_root: Path = Path("extracted"),
) -> None:
    l_reader = PdfReader(str(listening_pdf))
    r_reader = PdfReader(str(reading_pdf))

    for spec in TEST_SPECS:
        test_dir = out_root / f"test-{spec.test_id:02d}"
        test_dir.mkdir(parents=True, exist_ok=True)

        _write_pdf_slice(l_reader, spec.listening_range, test_dir / "source_listening.pdf")
        _write_pdf_slice(r_reader, spec.reading_range, test_dir / "source_reading.pdf")
        _write_ocr_dump(l_reader, spec.listening_range, test_dir / "ocr_listening.txt")
        _write_ocr_dump(r_reader, spec.reading_range, test_dir / "ocr_reading.txt")

        records = extract_test_images(
            reader=l_reader,
            test_id=spec.test_id,
            listening_range=spec.listening_range,
            part1_pages=spec.part1_pages,
            out_dir=test_dir / "images",
            pages_dir=test_dir / "pages",
        )
        print(
            f"Prepared test-{spec.test_id:02d}: "
            f"L pp.{spec.listening_range[0]}-{spec.listening_range[1]}, "
            f"R pp.{spec.reading_range[0]}-{spec.reading_range[1]}, "
            f"{len(records)} images"
        )


def main() -> None:
    prepare_all_tests()


if __name__ == "__main__":
    main()
