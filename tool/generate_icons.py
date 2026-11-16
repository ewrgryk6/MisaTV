#!/usr/bin/env python3
"""Regenerate every MisaTV icon asset from one procedural master.

Design (2026-11 redesign): an original, Netflix-*style* mark — a bold red
"M" (for MisaTV) with a darker-red ribbon shadow on pure black, the lower
edge bent into a gentle cinema-screen arch. It is NOT the Netflix "N" and
must not be presented as affiliated with Netflix; only the red-on-black
cinematic colour language is shared.

Usage:
    pip install pillow
    python tool/generate_icons.py

Outputs (all derived from the same 1024px master):
    assets/images/app_icon.png                  256
    docs/icon/misatv-icon-1024.png              1024
    windows/runner/resources/app_icon.ico       16/24/32/48/64/128/256
    android/app/src/main/res/mipmap-*/ic_launcher.png
    web/favicon.png                             32
    web/icons/Icon-192.png / Icon-512.png
    web/icons/Icon-maskable-192.png / -512.png  (mark padded to ~78%)
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RED = (229, 9, 20)       # cinematic red
DARK_RED = (140, 4, 10)  # ribbon shadow
BLACK = (10, 10, 10)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]


def find_font() -> str:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    sys.exit("No bold sans font found; add one to FONT_CANDIDATES.")


def render_mark(size: int) -> Image.Image:
    """Draw the red 'M' with ribbon shadow on a transparent layer."""
    ss = 4  # supersample
    w = size * ss
    layer = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = ImageFont.truetype(find_font(), int(w * 0.78))
    for dx, dy, colour in (
        (int(w * 0.018), int(w * 0.022), DARK_RED + (255,)),
        (0, 0, RED + (255,)),
    ):
        draw.text((w / 2 + dx, w / 2 + dy), "M", font=font, anchor="mm", fill=colour)
    return layer.resize((size, size), Image.LANCZOS)


def apply_arch(mark: Image.Image) -> Image.Image:
    """Bend the lower part upward toward the centre (cinema-screen arch)."""
    size = mark.size[0]
    src = mark.load()
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dst = out.load()
    for y in range(size):
        bend = (y / size) ** 2 * size * 0.045
        for x in range(size):
            shift = int(bend * math.sin(math.pi * x / size))
            sy = y + shift
            dst[x, y] = src[x, sy] if sy < size else (0, 0, 0, 0)
    return out


def master(size: int = 1024, mark_scale: float = 1.0) -> Image.Image:
    """Black square + arched mark. mark_scale < 1 pads the mark (maskable)."""
    bg = Image.new("RGBA", (size, size), BLACK + (255,))
    mark = apply_arch(render_mark(size))
    if mark_scale != 1.0:
        inner = int(size * mark_scale)
        mark = mark.resize((inner, inner), Image.LANCZOS)
        bg.alpha_composite(mark, ((size - inner) // 2, (size - inner) // 2))
    else:
        bg.alpha_composite(mark)
    return bg


def save(img: Image.Image, rel: str, size: int) -> None:
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.resize((size, size), Image.LANCZOS).save(path)
    print(f"  {rel} ({size}x{size})")


def main() -> None:
    full = master(1024)
    padded = master(1024, mark_scale=0.78)

    save(full, "docs/icon/misatv-icon-1024.png", 1024)
    save(full, "assets/images/app_icon.png", 256)
    save(full, "web/favicon.png", 32)
    save(full, "web/icons/Icon-192.png", 192)
    save(full, "web/icons/Icon-512.png", 512)
    save(padded, "web/icons/Icon-maskable-192.png", 192)
    save(padded, "web/icons/Icon-maskable-512.png", 512)

    for density, px in (
        ("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
        ("xxhdpi", 144), ("xxxhdpi", 192),
    ):
        save(full, f"android/app/src/main/res/mipmap-{density}/ic_launcher.png", px)

    ico_path = os.path.join(ROOT, "windows/runner/resources/app_icon.ico")
    full.save(ico_path, format="ICO",
              sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print("  windows/runner/resources/app_icon.ico (16-256)")


if __name__ == "__main__":
    main()
