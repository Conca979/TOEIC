# Hackers TOEIC 3 Interactive Web Platform

Static, responsive web application for practicing all 10 full-length Hackers TOEIC 3 tests with official section timers, ETS scaled scoring (`10-990`), Listening script toggles, and `localStorage` persistence.

## Features

- 10 independent TOEIC test datasets (`extracted/test-01/test.json` through `extracted/test-10/test.json`) covering 2,000 questions across Listening (Parts 1-4) and Reading (Parts 5-7).
- Official timed mode (`45:00` Listening + `75:00` Reading) and untimed practice mode.
- Standard raw-to-scaled scoring (`5-495` per section, `10-990` total) with per-part accuracy breakdown and Review Mode.
- Global and per-item Listening Script toggles with editable personal transcript notes and optional Blind Listening mode.
- Automatic `localStorage` persistence for answers, flags, timers, audio position, transcript notes, and attempt history, plus JSON export/import.

## Project Layout

- `index.html`, `styles.css`, `app.js`: zero-build static web application.
- `extracted/index.json`: catalog of all 10 tests.
- `extracted/test-XX/test.json` and `extracted/test-XX/images/`: per-test questions, passages, answer keys, and cropped Listening visuals.
- `Hacker 3/AUDIO/TEST 1.mp3` ... `TEST 10.mp3`: full-length Listening audio tracks.
- `src/toeic/`: Python extraction and validation utilities (`extract_images.py`, `prepare_tests.py`, `validate_test.py`).
- `.github/workflows/deploy.yml`: GitHub Actions workflow for deploying `_site/` to GitHub Pages.

## Local Development

Serve the repository root with any static HTTP server:

```sh
uv run python -m http.server 8123 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8123/` in your browser.

## Validation

Run the dataset schema validator across all 10 tests:

```sh
uv run python -m toeic.validate_test --all
```
