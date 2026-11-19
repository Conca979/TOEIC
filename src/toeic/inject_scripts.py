from __future__ import annotations

import json
import re
from pathlib import Path

HEADING_RE = re.compile(
    r"^(?:"
    r"(?:#+\s*)?(?:\*\*)?Number\s+(\d{1,2})(?:\*\*)?\.?\s*(.*)"
    r"|(?:\*\*)(\d{1,2})\.(?:\*\*)?\s*(.*)"
    r"|(?:#+\s*|\*\*)Questions?\s+(\d{2})\s*(?:through|[-–—])\s*(\d{2,3})\b.*"
    r")$",
    re.IGNORECASE,
)

QUESTION_BULLET_RE = re.compile(
    r"^\s*[-*]?\s*(?:\*\*)?(?:Number\s+)?(\d{2,3})\.\*?\*?\s+",
    re.IGNORECASE,
)

NOISE_LINE_RE = re.compile(
    r"^\s*(?:---+|##\s*Part\s+\d.*|\*\*Directions:.*|\*?\(?Go on to the next page\.?\)?\*?)\s*$",
    re.IGNORECASE,
)


def _clean_markdown_line(line: str) -> str:
    s = line.strip()
    if s.startswith(">"):
        s = s.lstrip(">").strip()
    s = re.sub(r"^[-*]\s+", "", s)
    s = s.replace("**", "")
    # Normalize leading italicized/escaped markers while keeping inline emphasis clean
    s = re.sub(r"^\*(.+)\*$", r"\1", s)
    return s.strip()


def parse_script_md(md_text: str) -> dict[str, str]:
    """Parse Part 1-4 scripts from a test's script.md keyed by 'q1'..'q31' and 'q32-34'..'q98-100'."""
    m_start = re.search(r"Now,?\s+Part\s+1\s+will\s+begin\.?", md_text, re.IGNORECASE)
    body = md_text[m_start.end() :] if m_start else md_text

    sections: list[tuple[str, list[str]]] = []
    current_key: str | None = None
    current_lines: list[str] = []

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if NOISE_LINE_RE.match(line):
            continue

        # Skip Part 1 "Look at the picture marked number X..." intro sentence if standalone
        m = HEADING_RE.match(line.strip())
        if m:
            num_a, rest_a, num_b, rest_b, grp_a, grp_b = m.groups()
            if num_a or num_b:
                q_num = int(num_a or num_b)
                if 1 <= q_num <= 31:
                    if current_key is not None:
                        sections.append((current_key, current_lines))
                    current_key = f"q{q_num}"
                    current_lines = []
                    rest = re.sub(r"^[\s*]+", "", (rest_a or rest_b or "")).strip()
                    if rest and not re.match(r"^Look at the picture marked number \d+", rest, re.I):
                        current_lines.append(_clean_markdown_line(rest))
                    continue
            elif grp_a and grp_b:
                g_start, g_end = int(grp_a), int(grp_b)
                if g_start >= 32:
                    if current_key is not None:
                        sections.append((current_key, current_lines))
                    current_key = f"q{g_start:02d}-{g_end:02d}"
                    current_lines = []
                    continue

        if current_key is None:
            continue

        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^Look at the picture marked number \d+", stripped, re.I):
            continue
        if current_key.startswith("q") and "-" in current_key:
            # Strip trailing repeated question prompts inside Part 3/4 script blocks
            qm = QUESTION_BULLET_RE.match(stripped)
            if qm:
                continue

        cleaned = _clean_markdown_line(stripped)
        if cleaned:
            current_lines.append(cleaned)

    if current_key is not None:
        sections.append((current_key, current_lines))

    return {key: "\n".join(lines) for key, lines in sections}


def inject_all_scripts(out_root: Path = Path("extracted")) -> None:
    for t in range(1, 11):
        test_dir = out_root / f"test-{t:02d}"
        script_path = test_dir / "script.md"
        json_path = test_dir / "test.json"

        parsed = parse_script_md(script_path.read_text(encoding="utf-8"))
        data = json.loads(json_path.read_text(encoding="utf-8"))

        missing_keys: list[str] = []
        for item in data["listening"]["part1"]:
            key = f"q{item['number']}"
            val = parsed.get(key, "").strip()
            if not val:
                missing_keys.append(key)
            item["script"] = val

        for item in data["listening"]["part2"]:
            key = f"q{item['number']}"
            val = parsed.get(key, "").strip()
            if not val:
                missing_keys.append(key)
            item["script"] = val

        for grp in data["listening"]["part3"]:
            key = grp["group_id"]
            val = parsed.get(key, "").strip()
            if not val:
                missing_keys.append(key)
            grp["script"] = val

        for grp in data["listening"]["part4"]:
            key = grp["group_id"]
            val = parsed.get(key, "").strip()
            if not val:
                missing_keys.append(key)
            grp["script"] = val

        if missing_keys:
            raise RuntimeError(f"Test {t:02d} missing scripts for: {missing_keys}")

        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Injected 54/54 scripts into {json_path}")


def main() -> None:
    inject_all_scripts()


if __name__ == "__main__":
    main()
