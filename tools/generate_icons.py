"""
Generate the PWA / favicon icon set with Pillow only (no external fonts or
image assets, so this runs identically on any machine).

Produces, under ASPNETApplication/wwwroot/icons/:
    icon-192.png
    icon-512.png
    icon-maskable-512.png
    apple-touch-icon.png   (180x180)

Run with:
    tools/.venv/bin/python tools/generate_icons.py
"""

import os
from PIL import Image, ImageDraw

BG_COLOR = (30, 41, 59, 255)      # #1E293B - dark navy
GLYPH_COLOR = (13, 148, 136, 255)  # #0D9488 - teal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "ASPNETApplication", "wwwroot", "icons"))


def draw_box_glyph(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float,
                    color, cutout_color):
    """Draw a simple flat 'inventory box / package' glyph, centered at (cx, cy)."""
    half = size / 2

    body_top = cy - half * 0.30
    body_bottom = cy + half
    body_left = cx - half
    body_right = cx + half
    radius = size * 0.09

    draw.rounded_rectangle(
        [body_left, body_top, body_right, body_bottom],
        radius=radius, fill=color,
    )

    # Open lid flaps at the top corners.
    flap_h = half * 0.55
    draw.polygon(
        [
            (body_left, body_top),
            (cx - size * 0.05, body_top),
            (body_left - half * 0.18, body_top - flap_h),
        ],
        fill=color,
    )
    draw.polygon(
        [
            (body_right, body_top),
            (cx + size * 0.05, body_top),
            (body_right + half * 0.18, body_top - flap_h),
        ],
        fill=color,
    )

    # Packing-tape seam: vertical + horizontal cut-outs in the background shade.
    seam_w = size * 0.055
    draw.rectangle(
        [cx - seam_w / 2, body_top, cx + seam_w / 2, body_bottom],
        fill=cutout_color,
    )
    tape_h = size * 0.045
    draw.rectangle(
        [body_left, body_top, body_right, body_top + tape_h],
        fill=cutout_color,
    )


def make_icon(size: int, *, rounded: bool, padding_ratio: float) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if rounded:
        corner_radius = size * 0.20
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=corner_radius, fill=BG_COLOR)
    else:
        # Maskable / apple-touch icons: full-bleed solid square, no built-in
        # rounding — the OS applies its own mask/corner treatment.
        draw.rectangle([0, 0, size - 1, size - 1], fill=BG_COLOR)

    glyph_size = size * (1 - 2 * padding_ratio)
    draw_box_glyph(draw, size / 2, size / 2, glyph_size, GLYPH_COLOR, BG_COLOR)

    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    icons = {
        "icon-192.png": make_icon(192, rounded=True, padding_ratio=0.16),
        "icon-512.png": make_icon(512, rounded=True, padding_ratio=0.16),
        # Maskable icon: keep a 20% safe-zone padding on every side so the
        # glyph survives circular/rounded-square OS masking.
        "icon-maskable-512.png": make_icon(512, rounded=False, padding_ratio=0.20),
        "apple-touch-icon.png": make_icon(180, rounded=False, padding_ratio=0.16),
    }

    for name, img in icons.items():
        path = os.path.join(OUT_DIR, name)
        img.save(path, "PNG")
        print(f"wrote {path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
