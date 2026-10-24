#!/usr/bin/env python3
"""Generate the GitHub social preview PNG (1280x640) for the HuLang repo.

The image shows up as the OG card when the repo URL is shared on
Twitter/X, HN, Slack, etc., and inside GitHub's repo header when set
via Settings -> Social preview.

Run:    python3 .github/generate_social_preview.py
Output: .github/social-preview.png
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1280, 640

BG = (13, 17, 23)
FG = (230, 237, 243)
DIM = (139, 148, 158)
ACCENT = (88, 166, 255)
GREEN = (63, 185, 80)
PINK = (255, 123, 114)
PANEL = (22, 27, 34)
PANEL_BORDER = (48, 54, 61)


def find_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    out = Path(__file__).resolve().parent / "social-preview.png"

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    sans_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    sans_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    mono_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    mono_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    ]

    title_font = find_font(sans_bold, 130)
    tag_font = find_font(sans_regular, 38)
    quote_font = find_font(sans_regular, 26)
    code_font = find_font(mono_regular, 26)
    code_bold = find_font(mono_bold, 26)
    label_font = find_font(sans_regular, 18)

    margin = 70

    draw.text((margin, 70), "HuLang", font=title_font, fill=FG)
    draw.text((margin, 215), "the human language compiler", font=tag_font, fill=ACCENT)

    panel_top = 295
    panel_bottom = 480
    panel_left = margin
    panel_right = WIDTH - margin
    draw.rounded_rectangle(
        [panel_left, panel_top, panel_right, panel_bottom],
        radius=14,
        fill=PANEL,
        outline=PANEL_BORDER,
        width=2,
    )

    inner = panel_left + 28
    line_y = panel_top + 24
    draw.text((inner, line_y), "$ ", font=code_font, fill=DIM)
    draw.text((inner + 28, line_y), "nlc build", font=code_bold, fill=GREEN)
    draw.text((inner + 28 + 134, line_y), " hello.txt", font=code_font, fill=FG)

    line_y += 44
    cursor_x = inner
    pieces = [
        ("  hello.txt ", DIM, code_font),
        ("-> ", ACCENT, code_font),
        ("[LLM] ", FG, code_font),
        ("-> ", ACCENT, code_font),
        ("C source ", FG, code_font),
        ("-> ", ACCENT, code_font),
        ("gcc ", FG, code_font),
        ("-> ", ACCENT, code_font),
        ("./hello", GREEN, code_bold),
        ("  (a real ELF binary)", DIM, code_font),
    ]
    for txt, color, font in pieces:
        draw.text((cursor_x, line_y), txt, font=font, fill=color)
        bbox = draw.textbbox((cursor_x, line_y), txt, font=font)
        cursor_x = bbox[2]

    line_y += 50
    draw.text((inner, line_y), "$ ", font=code_font, fill=DIM)
    draw.text((inner + 28, line_y), "./hello", font=code_bold, fill=GREEN)

    line_y += 36
    draw.text((inner, line_y), "Hello, World!", font=code_font, fill=FG)

    quote_y = HEIGHT - 80
    draw.text(
        (margin, quote_y),
        "Full type safety. The types are vibes.",
        font=quote_font,
        fill=PINK,
    )

    label_text = "github.com/BrendanWalsh/HuLang"
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text(
        (WIDTH - margin - label_w, HEIGHT - 50),
        label_text,
        font=label_font,
        fill=DIM,
    )

    img.save(out, "PNG", optimize=True)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
