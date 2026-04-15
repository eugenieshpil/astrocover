from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent

TITLE_FONT_CANDIDATES = [
    str(BASE_DIR / "fonts" / "PlayfairDisplay-Black.ttf"),
]

BODY_FONT_CANDIDATES = [
    str(BASE_DIR / "fonts" / "Inter_24pt-Regular.ttf"),
]


def load_font(candidates: Sequence[str], size: int):
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    raise FileNotFoundError(f"Font not found. Checked: {candidates}")


def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def fit_single_line_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    candidates: Sequence[str],
    max_width: int,
    start_size: int,
    min_size: int = 32,
):
    for size in range(start_size, min_size - 1, -2):
        font = load_font(candidates, size)
        if text_width(draw, text, font) <= max_width:
            return font
    return load_font(candidates, min_size)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    font,
    fill: tuple[int, int, int, int],
    shadow_fill: tuple[int, int, int, int] | None = None,
    shadow_offset: int = 3,
) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = int(center_x - w / 2)

    if shadow_fill is not None:
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_fill)

    draw.text((x, y), text, font=font, fill=fill)
    return h


def build_cover(
    cover_path: Path | str,
    output_path: Path | str,
    name: str,
    birth_date: str,
    birth_time: str,
    birth_place: str,
    prepared_date: str,
) -> None:
    cover_path = Path(cover_path)
    output_path = Path(output_path)

    img = Image.open(cover_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    width, height = img.size
    center_x = width // 2

    main_fill = (246, 249, 255, 255)
    shadow_fill = (0, 0, 0, 175)

    # Wider safe area for large cover typography
    max_title_width = int(width * 0.78)
    max_subtitle_width = int(width * 0.82)

    # Large title fonts
    name_font = fit_single_line_font(
        draw,
        f"{name},",
        TITLE_FONT_CANDIDATES,
        max_title_width,
        start_size=120,
        min_size=56,
    )

    subtitle_font = fit_single_line_font(
        draw,
        "here is your personal reading",
        TITLE_FONT_CANDIDATES,
        max_subtitle_width,
        start_size=92,
        min_size=44,
    )

    # Metadata / tagline
    body_font = load_font(BODY_FONT_CANDIDATES, 44)
    prepared_font = load_font(BODY_FONT_CANDIDATES, 42)
    tagline_font = fit_single_line_font(
        draw,
        "Move with it.",
        TITLE_FONT_CANDIDATES,
        int(width * 0.55),
        start_size=72,
        min_size=38,
    )

    # Move the whole composition much higher
    y = int(height * 0.47)

    # Name
    h = draw_centered_text(
        draw=draw,
        text=f"{name},",
        center_x=center_x,
        y=y,
        font=name_font,
        fill=main_fill,
        shadow_fill=shadow_fill,
        shadow_offset=4,
    )
    y += h + 18

    # Main title
    h = draw_centered_text(
        draw=draw,
        text="here is your personal reading",
        center_x=center_x,
        y=y,
        font=subtitle_font,
        fill=main_fill,
        shadow_fill=shadow_fill,
        shadow_offset=4,
    )
    y += h + 48

    # Metadata block with much larger spacing
    meta_lines = [
        f"Date of birth: {birth_date}",
        f"Time: {birth_time}",
        f"Place: {birth_place}",
    ]

    for line in meta_lines:
        h = draw_centered_text(
            draw=draw,
            text=line,
            center_x=center_x,
            y=y,
            font=body_font,
            fill=main_fill,
            shadow_fill=shadow_fill,
            shadow_offset=2,
        )
        y += h + 18

    y += 14

    # Prepared date
    h = draw_centered_text(
        draw=draw,
        text=f"Prepared on {prepared_date}",
        center_x=center_x,
        y=y,
        font=prepared_font,
        fill=main_fill,
        shadow_fill=shadow_fill,
        shadow_offset=2,
    )
    y += h + 44

    # Tagline
    draw_centered_text(
        draw=draw,
        text="Move with it.",
        center_x=center_x,
        y=y,
        font=tagline_font,
        fill=main_fill,
        shadow_fill=shadow_fill,
        shadow_offset=3,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a personalized cover image for the astrology reading PDF.")
    parser.add_argument("--cover", default=str(BASE_DIR / "cover.png"), help="Path to the base A4 cover image.")
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
