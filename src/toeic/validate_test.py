from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_4 = ("A", "B", "C", "D")
VALID_3 = ("A", "B", "C")


def _is_nonempty_str(val: Any) -> bool:
    return isinstance(val, str) and len(val.strip()) > 0


def _is_missing_marker(val: Any) -> bool:
    return isinstance(val, str) and val.strip().startswith("[missing")


def _check_options(opts: Any, keys: tuple[str, ...], ctx: str, errors: list[str]) -> None:
    if not isinstance(opts, dict):
        errors.append(f"{ctx}: options must be an object")
        return
    if set(opts.keys()) != set(keys):
        errors.append(f"{ctx}: options keys must be {list(keys)}, got {sorted(opts.keys())}")
        return
    for k in keys:
        if not _is_nonempty_str(opts.get(k)):
            errors.append(f"{ctx}: option {k} must be a non-empty string")


def _check_image_ref(img: Any, test_dir: Path, ctx: str, errors: list[str], allow_none: bool = False) -> None:
    if img is None:
        if not allow_none:
            errors.append(f"{ctx}: image is required (use path or '[missing...]')")
        return
    if not _is_nonempty_str(img):
        errors.append(f"{ctx}: image must be a non-empty string or null")
        return
    if _is_missing_marker(img):
        return
    if not (test_dir / img).is_file():
        errors.append(f"{ctx}: image file not found: {test_dir / img}")


def _check_question_4(q: Any, expected_num: int, ctx: str, errors: list[str]) -> None:
    if not isinstance(q, dict):
        errors.append(f"{ctx}: item must be an object")
        return
    if q.get("number") != expected_num:
        errors.append(f"{ctx}: expected number {expected_num}, got {q.get('number')!r}")
    if not _is_nonempty_str(q.get("question")):
        errors.append(f"{ctx}: question must be a non-empty string")
    _check_options(q.get("options"), VALID_4, ctx, errors)
    if q.get("answer") not in VALID_4:
        errors.append(f"{ctx}: answer must be in {VALID_4}, got {q.get('answer')!r}")
    if not _is_nonempty_str(q.get("explanation")):
        errors.append(f"{ctx}: explanation must be a non-empty string")


def validate_test(test_id: int, out_root: Path = Path("extracted")) -> list[str]:
    errors: list[str] = []
    test_dir = out_root / f"test-{test_id:02d}"
    json_path = test_dir / "test.json"
    if not json_path.is_file():
        return [f"Missing file: {json_path}"]

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON in {json_path}: {exc}"]

    if not isinstance(data, dict):
        return [f"{json_path}: root must be a JSON object"]

    if data.get("test_id") != test_id:
        errors.append(f"test_id must be {test_id}, got {data.get('test_id')!r}")
    if not _is_nonempty_str(data.get("title")):
        errors.append("title must be a non-empty string")
    audio_file = data.get("audio_file")
    if not _is_nonempty_str(audio_file):
        errors.append("audio_file must be a non-empty string")
    elif not _is_missing_marker(audio_file) and not Path(audio_file).is_file():
        errors.append(f"audio_file does not exist: {audio_file}")

    if not isinstance(data.get("missing_notes"), list) or not all(
        isinstance(x, str) for x in data.get("missing_notes", [])
    ):
        errors.append("missing_notes must be a list of strings")

    listening = data.get("listening")
    if not isinstance(listening, dict):
        errors.append("listening must be an object")
    else:
        # Part 1: 1..6
        p1 = listening.get("part1")
        if not isinstance(p1, list) or len(p1) != 6:
            errors.append(f"listening.part1 must have 6 items, got {len(p1) if isinstance(p1, list) else type(p1).__name__}")
        else:
            for idx, item in enumerate(p1, start=1):
                ctx = f"listening.part1[{idx}]"
                if not isinstance(item, dict):
                    errors.append(f"{ctx}: must be an object")
                    continue
                if item.get("number") != idx:
                    errors.append(f"{ctx}: expected number {idx}, got {item.get('number')!r}")
                _check_image_ref(item.get("image"), test_dir, ctx, errors, allow_none=False)
                _check_options(item.get("options"), VALID_4, ctx, errors)
                if item.get("answer") not in VALID_4:
                    errors.append(f"{ctx}: answer must be in {VALID_4}, got {item.get('answer')!r}")
                if not _is_nonempty_str(item.get("script")):
                    errors.append(f"{ctx}: script must be a non-empty string")
                if not _is_nonempty_str(item.get("explanation")):
                    errors.append(f"{ctx}: explanation must be a non-empty string")

        # Part 2: 7..31
        p2 = listening.get("part2")
        if not isinstance(p2, list) or len(p2) != 25:
            errors.append(f"listening.part2 must have 25 items, got {len(p2) if isinstance(p2, list) else type(p2).__name__}")
        else:
            for idx, item in enumerate(p2, start=7):
                ctx = f"listening.part2[q{idx}]"
                if not isinstance(item, dict):
                    errors.append(f"{ctx}: must be an object")
                    continue
                if item.get("number") != idx:
                    errors.append(f"{ctx}: expected number {idx}, got {item.get('number')!r}")
                _check_options(item.get("options"), VALID_3, ctx, errors)
                if item.get("answer") not in VALID_3:
                    errors.append(f"{ctx}: answer must be in {VALID_3}, got {item.get('answer')!r}")
                if not _is_nonempty_str(item.get("script")):
                    errors.append(f"{ctx}: script must be a non-empty string")
                if not _is_nonempty_str(item.get("explanation")):
                    errors.append(f"{ctx}: explanation must be a non-empty string")

        # Part 3: 13 groups (32..70)
        p3 = listening.get("part3")
        if not isinstance(p3, list) or len(p3) != 13:
            errors.append(f"listening.part3 must have 13 groups, got {len(p3) if isinstance(p3, list) else type(p3).__name__}")
        else:
            expected_q = 32
            for g in p3:
                expected_gid = f"q{expected_q:02d}-{expected_q + 2:02d}"
                ctx = f"listening.part3.{expected_gid}"
                if not isinstance(g, dict):
                    errors.append(f"{ctx}: group must be an object")
                    expected_q += 3
                    continue
                if g.get("group_id") != expected_gid:
                    errors.append(f"{ctx}: expected group_id {expected_gid!r}, got {g.get('group_id')!r}")
                if not _is_nonempty_str(g.get("script")):
                    errors.append(f"{ctx}: script must be a non-empty string")
                _check_image_ref(g.get("image"), test_dir, ctx, errors, allow_none=True)
                qs = g.get("questions")
                if not isinstance(qs, list) or len(qs) != 3:
                    errors.append(f"{ctx}: must have 3 questions")
                else:
                    has_graphic_prompt = False
                    for q in qs:
                        _check_question_4(q, expected_q, f"{ctx}.q{expected_q}", errors)
                        if isinstance(q, dict) and isinstance(q.get("question"), str) and "look at the graphic" in q["question"].lower():
                            has_graphic_prompt = True
                        expected_q += 1
                    if has_graphic_prompt and g.get("image") is None:
                        errors.append(f"{ctx}: has 'Look at the graphic' question but image is null")
                    continue
                expected_q += 3

        # Part 4: 10 groups (71..100)
        p4 = listening.get("part4")
        if not isinstance(p4, list) or len(p4) != 10:
            errors.append(f"listening.part4 must have 10 groups, got {len(p4) if isinstance(p4, list) else type(p4).__name__}")
        else:
            expected_q = 71
            for g in p4:
                expected_gid = f"q{expected_q:02d}-{expected_q + 2:02d}"
                ctx = f"listening.part4.{expected_gid}"
                if not isinstance(g, dict):
                    errors.append(f"{ctx}: group must be an object")
                    expected_q += 3
                    continue
                if g.get("group_id") != expected_gid:
                    errors.append(f"{ctx}: expected group_id {expected_gid!r}, got {g.get('group_id')!r}")
                if not _is_nonempty_str(g.get("script")):
                    errors.append(f"{ctx}: script must be a non-empty string")
                _check_image_ref(g.get("image"), test_dir, ctx, errors, allow_none=True)
                qs = g.get("questions")
                if not isinstance(qs, list) or len(qs) != 3:
                    errors.append(f"{ctx}: must have 3 questions")
                else:
                    has_graphic_prompt = False
                    for q in qs:
                        _check_question_4(q, expected_q, f"{ctx}.q{expected_q}", errors)
                        if isinstance(q, dict) and isinstance(q.get("question"), str) and "look at the graphic" in q["question"].lower():
                            has_graphic_prompt = True
                        expected_q += 1
                    if has_graphic_prompt and g.get("image") is None:
                        errors.append(f"{ctx}: has 'Look at the graphic' question but image is null")
                    continue
                expected_q += 3

    reading = data.get("reading")
    if not isinstance(reading, dict):
        errors.append("reading must be an object")
    else:
        # Part 5: 30 items (101..130)
        p5 = reading.get("part5")
        if not isinstance(p5, list) or len(p5) != 30:
            errors.append(f"reading.part5 must have 30 items, got {len(p5) if isinstance(p5, list) else type(p5).__name__}")
        else:
            for idx, item in enumerate(p5, start=101):
                _check_question_4(item, idx, f"reading.part5.q{idx}", errors)

        # Part 6: 4 groups (131..146)
        p6 = reading.get("part6")
        if not isinstance(p6, list) or len(p6) != 4:
            errors.append(f"reading.part6 must have 4 groups, got {len(p6) if isinstance(p6, list) else type(p6).__name__}")
        else:
            expected_q = 131
            for g in p6:
                expected_gid = f"q{expected_q}-{expected_q + 3}"
                ctx = f"reading.part6.{expected_gid}"
                if not isinstance(g, dict):
                    errors.append(f"{ctx}: group must be an object")
                    expected_q += 4
                    continue
                if g.get("group_id") != expected_gid:
                    errors.append(f"{ctx}: expected group_id {expected_gid!r}, got {g.get('group_id')!r}")
                if not _is_nonempty_str(g.get("directions")):
                    errors.append(f"{ctx}: directions must be a non-empty string")
                if not _is_nonempty_str(g.get("passage")):
                    errors.append(f"{ctx}: passage must be a non-empty string")
                qs = g.get("questions")
                if not isinstance(qs, list) or len(qs) != 4:
                    errors.append(f"{ctx}: must have 4 questions")
                    expected_q += 4
                else:
                    for q in qs:
                        _check_question_4(q, expected_q, f"{ctx}.q{expected_q}", errors)
                        expected_q += 1

        # Part 7: contiguous groups covering 147..200
        p7 = reading.get("part7")
        if not isinstance(p7, list) or len(p7) == 0:
            errors.append("reading.part7 must be a non-empty list of groups")
        else:
            expected_q = 147
            for g_idx, g in enumerate(p7):
                ctx = f"reading.part7[{g_idx}]"
                if not isinstance(g, dict):
                    errors.append(f"{ctx}: group must be an object")
                    continue
                if not _is_nonempty_str(g.get("group_id")):
                    errors.append(f"{ctx}: group_id must be a non-empty string")
                if not _is_nonempty_str(g.get("directions")):
                    errors.append(f"{ctx}: directions must be a non-empty string")
                passages = g.get("passages")
                if not isinstance(passages, list) or len(passages) == 0:
                    errors.append(f"{ctx}: passages must be a non-empty list")
                else:
                    for p_idx, p_obj in enumerate(passages):
                        p_ctx = f"{ctx}.passages[{p_idx}]"
                        if not isinstance(p_obj, dict):
                            errors.append(f"{p_ctx}: must be an object")
                            continue
                        if not _is_nonempty_str(p_obj.get("type")):
                            errors.append(f"{p_ctx}: type must be a non-empty string")
                        if not isinstance(p_obj.get("title"), str):
                            errors.append(f"{p_ctx}: title must be a string")
                        if not _is_nonempty_str(p_obj.get("content")):
                            errors.append(f"{p_ctx}: content must be a non-empty string")
                qs = g.get("questions")
                if not isinstance(qs, list) or len(qs) == 0:
                    errors.append(f"{ctx}: questions must be a non-empty list")
                else:
                    for q in qs:
                        _check_question_4(q, expected_q, f"{ctx}.q{expected_q}", errors)
                        expected_q += 1
            if expected_q != 201:
                errors.append(f"reading.part7 must end at question 200 (ended at {expected_q - 1})")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extracted TOEIC test JSON files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", type=int, help="Test number 1..10")
    group.add_argument("--all", action="store_true", help="Validate all 10 tests")
    parser.add_argument("--root", type=Path, default=Path("extracted"))
    args = parser.parse_args()

    tests = list(range(1, 11)) if args.all else [args.test]
    any_failed = False
    for t in tests:
        errs = validate_test(t, args.root)
        if errs:
            any_failed = True
            print(f"INVALID: test-{t:02d} ({len(errs)} error(s))")
            for e in errs[:30]:
                print(f"  - {e}")
            if len(errs) > 30:
                print(f"  ... and {len(errs) - 30} more")
        else:
            print(f"VALID: test-{t:02d} (200/200 questions verified)")

    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
