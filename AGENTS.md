# Project Overview

TOEIC interactive learning platform built from local Hacker 3 PDF and MP3 resources in `Hacker 3/`.

## Environment and Tooling

- Python project managed with `uv` (`pyproject.toml`, `uv.lock`, Python `>=3.10`).
- Dependencies: `pypdf`, `pillow`, `numpy`.
- Run scripts via `uv run python -m ...`.

## Source Data Notes

- `Hacker 3/HAKER 3 LISTENING.pdf` (125 pages): each page stores one main full-page grayscale JPEG scan (`1234x1742`) plus a separate watermark overlay PNG in a nested Form XObject and an invisible OCR text layer (`3 Tr`). Extracting the main `/Image` XObject directly from `/Resources/XObject` avoids the overlay watermark.
- `Hacker 3/HACKER 3 READING.pdf` (290 pages): 29 pages per test across 10 tests (`pp. 1-29`, `30-58`, ..., `262-290`), combining vector text with embedded passage/layout images.
- Listening Tests 04-05 anomaly: pages 40-60 total 21 pages instead of 26:
  - Test 04 (`pp. 40-48`, 9 pages) originally omitted source pages for Listening Part 1 Q1-Q2, Part 3 Q65-Q70, and Part 4 Q71-Q82. Those missing items and graphics (`part1_q01.jpg`, `part1_q02.jpg`, `part3_q65-67.jpg`, `part3_q68-70.jpg`) have been simulated from `extracted/test-04/script.md` and aligned with official answers in `Hacker 3/Hacker 3 Key/AK-Listening-Test04.jpg` (marked `"simulated": true` in `extracted/test-04/test.json`).
  - Test 05 (`pp. 49-60`, 12 pages) is missing only its cover page.

## Architecture and Conventions

- `src/toeic/extract_images.py`: extracts Listening Part 1 photos and Part 3/4 boxed graphics into `extracted/test-XX/images/` along with `manifest.json`.
  - Part 1 uses row/column ink-density segmentation.
  - Part 3 and Part 4 detect outermost rectangular bordered graphics (with a column-band fallback) and map them to question groups via `"Look at the graphic"` occurrences in the OCR text layer.
- `src/toeic/prepare_tests.py`: deterministically slices `source_listening.pdf`, `source_reading.pdf`, `ocr_listening.txt`, `ocr_reading.txt`, `pages/`, and `images/` for all 10 tests (`extracted/test-01/` through `extracted/test-10/`).
- `src/toeic/inject_scripts.py`: parses `extracted/test-XX/script.md` (54 Listening scripts per test across Part 1-4) and injects `"script"` fields into `extracted/test-XX/test.json`.
- `src/toeic/simulate_test4.py`: generates Test 04's simulated Part 1 photos, Part 3 graphics, and Q1-Q2 / Q65-Q82 prompts/options from `extracted/test-04/script.md` and updates `manifest.json` and `extracted/index.json`.
- `src/toeic/validate_test.py`: validates the unified 200-question JSON contract (`--test N` or `--all`) across `listening` (`part1`..`part4`), `reading` (`part5`..`part7`), Listening `"script"` coverage (54/54), per-question `"explanation"` coverage (200/200), option completeness, answer validity (`A`-`D` / `A`-`C`), and image file existence.
- `src/toeic/trim_audio.py`: losslessly strips the 18.0-second (`689`-frame, `287,974`-byte) Korean intro/jingle immediately following the ID3v2 tag across `Hacker 3/AUDIO/TEST 1.mp3` through `TEST 10.mp3` (idempotent via intro prefix hash check).
- `extracted/index.json`: catalog of all 10 tests (`json_path`, `audio_file`, `question_count`, `image_count`, `complete`, `missing_notes`).
- `extracted/test-XX/test.json`: self-contained 200-question dataset per test with unified Listening + Reading structure, spoken `script` blocks, short per-question `explanation` strings, and relative image paths (`images/...`).

## Static Web Application and Deployment

- `index.html`, `styles.css`, `app.js`: pure static responsive web application (minimal white UI, zero build step) served from the repository root.
  - Loads `extracted/index.json` and per-test `extracted/test-XX/test.json`, images, and `Hacker 3/AUDIO/TEST X.mp3`.
  - Implements official ETS TOEIC timing (`45:00` Listening + `75:00` Reading) and scaled scoring (`5-495` per section, `10-990` total).
  - Includes a global/per-item Listening Script toggle (`<input type="checkbox" switch>`) displaying only the corresponding question/group script from `script.md`, optional Blind Listening mode, and a per-question bottom `Show Explanation` toggle across Parts 1-7.
  - Supports right-click answer cross-out and mobile right-edge `[x]` strike button (process of elimination) per option across all parts.
  - Persists progress in `localStorage` (`toeic_active_test`, `toeic_attempt_test_XX`, `toeic_scripts_test_XX`, `toeic_history`) with JSON export/import.
- `.github/workflows/deploy.yml`: GitHub Actions workflow assembling `_site/` (`index.html`, `styles.css`, `app.js`, `extracted/index.json`, `extracted/test-*/test.json`, `extracted/test-*/images/`, `Hacker 3/AUDIO/*.mp3`) and deploying to GitHub Pages.
