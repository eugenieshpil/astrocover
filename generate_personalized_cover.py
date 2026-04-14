#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont


TITLE_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
]
BODY_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]


def load_font(candidates: Sequence[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    candidates: Sequence[str],
    max_width: int,
    start_size: int,
    min_size: int = 20,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, list[str]]:
    for size in range(start_size, min_size - 1, -2):
        font = load_font(candidates, size)
        wrapped = wrap_text(draw, text, font, max_width)
        widest = 0
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            widest = max(widest, bbox[2] - bbox[0])
        if widest <= max_width:
            return font, wrapped
    font = load_font(candidates, min_size)
    return font, wrap_text(draw, text, font, max_width)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        bbox = draw.textbbox((0, 0), trial, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    center_x: int,
    start_y: int,
    font,
    fill: tuple[int, int, int, int],
    shadow_fill: tuple[int, int, int, int] | None = None,
    line_gap: int = 10,
    shadow_offset: int = 3,
) -> int:
    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = int(center_x - text_w / 2)
        if shadow_fill is not None:
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_fill)
        draw.text((x, y), line, font=font, fill=fill)
        y += text_h + line_gap
    return y


def build_cover(
    cover_path: Path,
    output_path: Path,
    name: str,
    birth_date: str,
    birth_time: str,
    birth_place: str,
    prepared_date: str,
) -> None:
    img = Image.open(cover_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    width, height = img.size
    center_x = width // 2
    safe_width = int(width * 0.72)

    title_text = f"{name}, here is your personal reading"
    title_font, title_lines = fit_text(
        draw=draw,
        text=title_text,
        candidates=TITLE_FONT_CANDIDATES,
        max_width=safe_width,
        start_size=58,
        min_size=28,
    )

    body_font = load_font(BODY_FONT_CANDIDATES, 28)
    small_font = load_font(BODY_FONT_CANDIDATES, 25)
    tagline_font = load_font(TITLE_FONT_CANDIDATES, 32)

    main_fill = (246, 249, 255, 255)
    shadow_fill = (0, 0, 0, 165)

    y = int(height * 0.60)
    y = draw_centered_lines(
        draw,
        title_lines,
        center_x,
        y,
        title_font,
        main_fill,
        shadow_fill=shadow_fill,
        line_gap=8,
        shadow_offset=3,
    )

    y += 26

    meta_lines = [
        f"Date of birth: {birth_date}",
        f"Time: {birth_time}",
        f"Place: {birth_place}",
    ]
    y = draw_centered_lines(
        draw,
        meta_lines,
        center_x,
        y,
        body_font,
        main_fill,
        shadow_fill=shadow_fill,
        line_gap=12,
        shadow_offset=2,
    )

    y += 18

    y = draw_centered_lines(
        draw,
        [f"Reading prepared: {prepared_date}"],
        center_x,
        y,
        small_font,
        main_fill,
        shadow_fill=shadow_fill,
        line_gap=8,
        shadow_offset=2,
    )

    y += 18

    draw_centered_lines(
        draw,
        ["Move with it."],
        center_x,
        y,
        tagline_font,
        main_fill,
        shadow_fill=shadow_fill,
        line_gap=8,
        shadow_offset=2,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a personalized cover image for the astrology reading PDF.")
    parser.add_argument("--cover", default="/mnt/data/cover.png", help="Path to the base A4 cover image.")
    parser.add_argument("--output", default="/mnt/data/personalized_cover.png", help="Output PNG path.")
    parser.add_argument("--name", default="{{name}}", help="Recipient name.")
    parser.add_argument("--birth-date", default="{{birth_date}}", help="Date of birth.")
    parser.add_argument("--birth-time", default="{{birth_time}}", help="Birth time.")
    parser.add_argument("--birth-place", default="{{birth_place}}", help="Birth place.")
    parser.add_argument("--prepared-date", default="{{generation_date}}", help="Reading prepared date.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_cover(
        cover_path=Path(args.cover),
        output_path=Path(args.output),
        name=args.name,
        birth_date=args.birth_date,
        birth_time=args.birth_time,
        birth_place=args.birth_place,
        prepared_date=args.prepared_date,
    )
    print(args.output)


if __name__ == "__main__":
    main()
