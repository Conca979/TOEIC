from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

Q01_SRC = Path(
    r"C:\Users\admin\.gemini\antigravity\brain\936eece6-4d5a-4c87-8b94-e12937d2932a\toeic_luggage_reach_v2_1795052476082.jpg"
)
Q02_SRC = Path(
    r"C:\Users\admin\.gemini\antigravity\brain\936eece6-4d5a-4c87-8b94-e12937d2932a\toeic_technician_ppe_1795052461066.jpg"
)

SIMULATED_Q_TEXT_AND_OPTIONS: dict[int, tuple[str, dict[str, str]]] = {
    # Part 3 (Q65-70)
    65: (
        "Where does the conversation most likely take place?",
        {
            "A": "In a conference room",
            "B": "In a furniture showroom",
            "C": "In a warehouse",
            "D": "In a cafeteria",
        },
    ),
    66: (
        "Look at the graphic. Which part is missing?",
        {
            "A": "Tabletop",
            "B": "Bolts",
            "C": "Support bar",
            "D": "Table legs",
        },
    ),
    67: (
        "What will the man probably do during his lunch break?",
        {
            "A": "Call customer service again",
            "B": "Buy replacement bolts",
            "C": "Meet with his manager",
            "D": "Move a table to another room",
        },
    ),
    68: (
        "Why did the woman miss the event?",
        {
            "A": "She was visiting a competitor's store",
            "B": "She had to prepare a board report",
            "C": "A meeting with an executive ran late",
            "D": "Her flight was delayed",
        },
    ),
    69: (
        "Look at the graphic. Which model will the woman give a presentation on?",
        {
            "A": "Model E-100",
            "B": "Model E-200",
            "C": "Model E-300",
            "D": "Model E-400",
        },
    ),
    70: (
        "What does the man offer to do?",
        {
            "A": "Attend the board meeting",
            "B": "Help gather information",
            "C": "Contact Saber Electronics",
            "D": "Redesign a product",
        },
    ),
    # Part 4 (Q71-82)
    71: (
        "Who most likely is the speaker?",
        {
            "A": "A police officer",
            "B": "A car mechanic",
            "C": "A hospital staff member",
            "D": "An airport security guard",
        },
    ),
    72: (
        "What does the speaker remind listeners to do?",
        {
            "A": "Pay a parking fee before leaving",
            "B": "Register their license plate numbers",
            "C": "Use the west exit during emergencies",
            "D": "Avoid parking in emergency areas",
        },
    ),
    73: (
        "According to the speaker, what should listeners look for?",
        {
            "A": "A four-door sedan",
            "B": "Colored pavement markings",
            "C": "Posted state regulations",
            "D": "Security personnel",
        },
    ),
    74: (
        'Why does the speaker say, "There\'s a massive snowstorm here"?',
        {
            "A": "To warn the listener about driving conditions",
            "B": "To cancel a business trip to Philadelphia",
            "C": "To request a weather update",
            "D": "To explain why her return flight is delayed",
        },
    ),
    75: (
        "According to the speaker, what did the listener do last year?",
        {
            "A": "Helped develop a software application",
            "B": "Gave a presentation to Techworth",
            "C": "Relocated to the Houston office",
            "D": "Trained an assistant",
        },
    ),
    76: (
        "What does the speaker suggest the listener do?",
        {
            "A": "Reschedule the 3:00 p.m. meeting",
            "B": "Contact Beth Richards if assistance is needed",
            "C": "Forward the files to Philadelphia",
            "D": "Wait until evening to confirm",
        },
    ),
    77: (
        "According to the speaker, what will happen in August?",
        {
            "A": "New employees will join the division",
            "B": "Old office furniture will be sold",
            "C": "Part of the office will be renovated",
            "D": "The company will move to a new building",
        },
    ),
    78: (
        "What is located on the fourth floor?",
        {
            "A": "Temporary workstations",
            "B": "Storage rooms for paint supplies",
            "C": "The IT support desk",
            "D": "Conference rooms",
        },
    ),
    79: (
        "What will most likely be done toward the end of this month?",
        {
            "A": "Painting will be completed",
            "B": "Work computers will be moved",
            "C": "Desks will be ordered",
            "D": "Noise tests will be conducted",
        },
    ),
    80: (
        "Where most likely does the speaker work?",
        {
            "A": "At a moving company",
            "B": "At an electronics retailer",
            "C": "At a security firm",
            "D": "At a delivery service",
        },
    ),
    81: (
        "What does the speaker instruct the listener to do?",
        {
            "A": "Leave a signed note on her door",
            "B": "Confirm her home address online",
            "C": "Pick up a package at a sorting facility",
            "D": "Pay a redelivery fee",
        },
    ),
    82: (
        "What does the speaker say might happen after seven days?",
        {
            "A": "A storage fee will be charged",
            "B": "A fourth delivery attempt will be made",
            "C": "The sorting facility will relocate",
            "D": "The parcel will be sent back to the sender",
        },
    ),
}


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf"]
        if bold
        else [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"]
    )
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _prepare_part1_photo(src: Path, dest: Path, target_size: tuple[int, int] = (718, 520)) -> tuple[int, int]:
    img = Image.open(src).convert("L")
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    img.save(dest, quality=94)
    return img.size


def _draw_q65_table(dest: Path) -> tuple[int, int]:
    w, h = 520, 260
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    f_title = _load_font(18, bold=True)
    f_head = _load_font(15, bold=True)
    f_row = _load_font(15, bold=False)

    draw.rectangle([8, 8, w - 9, h - 9], outline=30, width=2)
    draw.text((w // 2, 26), "Table Assembly — Parts List", fill=15, font=f_title, anchor="mm")

    left, top, right, bot = 22, 52, w - 22, h - 20
    row_h = (bot - top) // 5
    col_x1 = left + 160
    col_x2 = left + 230

    draw.rectangle([left, top, right, bot], outline=40, width=2)
    draw.rectangle([left, top, right, top + row_h], fill=235, outline=40, width=1)
    for i in range(1, 5):
        y = top + i * row_h
        draw.line([left, y, right, y], fill=60, width=1)
    draw.line([col_x1, top, col_x1, bot], fill=60, width=1)
    draw.line([col_x2, top, col_x2, bot], fill=60, width=1)

    headers = ["Part", "Qty", "Assembly Step"]
    rows = [
        ("Tabletop", "1", "Step 1: Attach to legs"),
        ("Table Legs", "4", "Step 1: Secure with bolts"),
        ("Bolts", "8", "Step 1: Fasten legs"),
        ("Support Bar", "1", "Step 2: Mount under frame"),
    ]

    draw.text((left + 12, top + row_h // 2), headers[0], fill=15, font=f_head, anchor="lm")
    draw.text(((col_x1 + col_x2) // 2, top + row_h // 2), headers[1], fill=15, font=f_head, anchor="mm")
    draw.text((col_x2 + 12, top + row_h // 2), headers[2], fill=15, font=f_head, anchor="lm")

    for idx, (part_name, qty, step) in enumerate(rows, start=1):
        yc = top + idx * row_h + row_h // 2
        draw.text((left + 12, yc), part_name, fill=20, font=f_row, anchor="lm")
        draw.text(((col_x1 + col_x2) // 2, yc), qty, fill=20, font=f_row, anchor="mm")
        draw.text((col_x2 + 12, yc), step, fill=20, font=f_row, anchor="lm")

    img.save(dest, quality=95)
    return img.size


def _draw_q68_chart(dest: Path) -> tuple[int, int]:
    w, h = 500, 290
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    f_title = _load_font(18, bold=True)
    f_lbl = _load_font(14, bold=False)
    f_val = _load_font(14, bold=True)

    draw.rectangle([8, 8, w - 9, h - 9], outline=30, width=2)
    draw.text((w // 2, 28), "Oven Models — Retail Price ($)", fill=15, font=f_title, anchor="mm")

    plot_l, plot_t, plot_r, plot_b = 70, 56, w - 28, h - 46
    draw.line([plot_l, plot_t, plot_l, plot_b], fill=30, width=2)
    draw.line([plot_l, plot_b, plot_r, plot_b], fill=30, width=2)

    max_val = 800
    for tick in (200, 400, 600, 800):
        y = plot_b - int((tick / max_val) * (plot_b - plot_t))
        draw.line([plot_l, y, plot_r, y], fill=190, width=1)
        draw.text((plot_l - 8, y), f"${tick}", fill=40, font=f_lbl, anchor="rm")

    models = [
        ("Model E-100", 420),
        ("Model E-200", 680),
        ("Model E-300", 510),
        ("Model E-400", 590),
    ]
    slot_w = (plot_r - plot_l) // len(models)
    bar_w = 56
    for idx, (name, price) in enumerate(models):
        cx = plot_l + slot_w * idx + slot_w // 2
        bar_h = int((price / max_val) * (plot_b - plot_t))
        bx1, bx2 = cx - bar_w // 2, cx + bar_w // 2
        by1 = plot_b - bar_h
        draw.rectangle([bx1, by1, bx2, plot_b], fill=175, outline=30, width=1)
        draw.text((cx, by1 - 10), f"${price}", fill=15, font=f_val, anchor="mm")
        draw.text((cx, plot_b + 18), name, fill=15, font=f_lbl, anchor="mm")

    img.save(dest, quality=95)
    return img.size


def simulate_test4(out_root: Path = Path("extracted")) -> None:
    test_dir = out_root / "test-04"
    img_dir = test_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    q1_w, q1_h = _prepare_part1_photo(Q01_SRC, img_dir / "part1_q01.jpg")
    q2_w, q2_h = _prepare_part1_photo(Q02_SRC, img_dir / "part1_q02.jpg")
    q65_w, q65_h = _draw_q65_table(img_dir / "part3_q65-67.jpg")
    q68_w, q68_h = _draw_q68_chart(img_dir / "part3_q68-70.jpg")

    json_path = test_dir / "test.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Part 1 Q1 & Q2
    for q_num, fname in ((1, "images/part1_q01.jpg"), (2, "images/part1_q02.jpg")):
        item = data["listening"]["part1"][q_num - 1]
        item["image"] = fname
        item["simulated"] = True

    # Part 3 Q65-67 & Q68-70
    for grp, fname in ((data["listening"]["part3"][11], "images/part3_q65-67.jpg"), (data["listening"]["part3"][12], "images/part3_q68-70.jpg")):
        grp["image"] = fname
        grp["simulated"] = True
        for q in grp["questions"]:
            prompt, opts = SIMULATED_Q_TEXT_AND_OPTIONS[q["number"]]
            q["question"] = prompt
            q["options"] = opts
            q["simulated"] = True

    # Part 4 Q71-82
    for grp in data["listening"]["part4"][:4]:
        grp["simulated"] = True
        for q in grp["questions"]:
            prompt, opts = SIMULATED_Q_TEXT_AND_OPTIONS[q["number"]]
            q["question"] = prompt
            q["options"] = opts
            q["simulated"] = True

    data["missing_notes"] = [
        "Source PDF pp. 40-48 omitted Listening Part 1 Q1-Q2, Part 3 Q65-Q70, and Part 4 Q71-Q82. "
        "Simulated questions, options, Part 1 photos, and Part 3 graphics have been generated from "
        "extracted/test-04/script.md and aligned with official answers in AK-Listening-Test04.jpg."
    ]

    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Update manifest.json with the 4 new simulated images in question order
    manifest_path = img_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_file = {m["file"]: m for m in manifest}
    new_entries = [
        {"test": 4, "part": 1, "questions": "q01", "page": 0, "bbox": [0, 0, q1_w, q1_h], "width": q1_w, "height": q1_h, "file": "part1_q01.jpg", "simulated": True},
        {"test": 4, "part": 1, "questions": "q02", "page": 0, "bbox": [0, 0, q2_w, q2_h], "width": q2_w, "height": q2_h, "file": "part1_q02.jpg", "simulated": True},
        {"test": 4, "part": 3, "questions": "q65-67", "page": 0, "bbox": [0, 0, q65_w, q65_h], "width": q65_w, "height": q65_h, "file": "part3_q65-67.jpg", "simulated": True},
        {"test": 4, "part": 3, "questions": "q68-70", "page": 0, "bbox": [0, 0, q68_w, q68_h], "width": q68_w, "height": q68_h, "file": "part3_q68-70.jpg", "simulated": True},
    ]
    for entry in new_entries:
        by_file[entry["file"]] = entry

    ordered = sorted(by_file.values(), key=lambda m: (m["part"], m["questions"]))
    manifest_path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")

    # Update extracted/index.json
    index_path = out_root / "index.json"
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    for entry in index_data["tests"]:
        if entry["test_id"] == 4:
            entry["image_count"] = len(ordered)
            entry["complete"] = True
            entry["missing_notes"] = data["missing_notes"]
    index_path.write_text(json.dumps(index_data, indent=2) + "\n", encoding="utf-8")

    print(f"Simulated Test 04 missing Q1-2, Q65-70, Q71-82 and wrote 4 images ({len(ordered)} total)")


def main() -> None:
    simulate_test4()


if __name__ == "__main__":
    main()
