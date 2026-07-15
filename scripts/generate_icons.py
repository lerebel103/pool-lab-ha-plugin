"""Generate brand icons for the Pool Lab integration.

Creates all required Home Assistant brand image variants programmatically.
No external artwork is needed — the icon is a simple pool-themed design
(water droplet) generated entirely with Pillow.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).parent
BRAND_DIR = SCRIPT_DIR.parent / "custom_components" / "pool_lab" / "brand"

# Brand colors
BG_COLOR = (0, 119, 182)  # Deep pool blue
ACCENT_COLOR = (72, 202, 228)  # Light water blue
WHITE = (255, 255, 255)


def create_icon(size: int) -> Image.Image:
    """Create a square icon with a water droplet design.

    Features a rounded-rectangle blue background with a stylized
    water droplet and wave, representing pool water management.
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Draw rounded rectangle background
    margin = int(size * 0.02)
    radius = int(size * 0.18)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(*BG_COLOR, 255),
    )

    # Draw a water droplet shape (teardrop)
    cx = size // 2
    # Position droplet in upper-center area
    drop_top = int(size * 0.18)
    drop_bottom = int(size * 0.62)
    drop_width = int(size * 0.28)

    # Build droplet as a polygon (pointed top, round bottom)
    points = []
    # Top point
    points.append((cx, drop_top))

    # Right curve down to bottom
    num_curve_points = 20
    for i in range(num_curve_points + 1):
        angle = -math.pi / 2 + math.pi * i / num_curve_points
        # Egg shape: wider at bottom
        progress = i / num_curve_points
        width_factor = math.sin(math.pi * progress) * (0.5 + 0.5 * progress)
        px = cx + int(drop_width * width_factor)
        py = drop_top + int((drop_bottom - drop_top) * progress)
        points.append((px, py))

    # Bottom semicircle
    bottom_cy = drop_bottom
    bottom_radius = int(drop_width * 0.85)
    for i in range(num_curve_points + 1):
        angle = 0 + math.pi * i / num_curve_points
        px = cx + int(bottom_radius * math.cos(angle))
        py = bottom_cy + int(bottom_radius * 0.5 * math.sin(angle))
        points.append((px, py))

    # Left curve back up
    for i in range(num_curve_points, -1, -1):
        angle = -math.pi / 2 + math.pi * i / num_curve_points
        progress = i / num_curve_points
        width_factor = math.sin(math.pi * progress) * (0.5 + 0.5 * progress)
        px = cx - int(drop_width * width_factor)
        py = drop_top + int((drop_bottom - drop_top) * progress)
        points.append((px, py))

    draw.polygon(points, fill=(*WHITE, 230))

    # Draw subtle wave lines at the bottom
    wave_y = int(size * 0.75)
    wave_amplitude = int(size * 0.03)
    wave_thickness = max(2, int(size * 0.02))

    for wave_offset in range(3):
        y_base = wave_y + wave_offset * int(size * 0.06)
        wave_points = []
        x_start = int(size * 0.2)
        x_end = int(size * 0.8)
        for x in range(x_start, x_end + 1, 2):
            y = y_base + int(wave_amplitude * math.sin((x - x_start) * 2 * math.pi / (size * 0.3)))
            wave_points.append((x, y))

        if len(wave_points) > 1:
            alpha = 200 - wave_offset * 50
            draw.line(wave_points, fill=(*ACCENT_COLOR, alpha), width=wave_thickness)

    return canvas


def create_logo(size_w: int, size_h: int) -> Image.Image:
    """Create a rectangular logo with the icon and text.

    Centers the droplet icon on the left with 'Pool Lab' text on the right.
    """
    canvas = Image.new("RGBA", (size_w, size_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Draw a smaller version of the icon on the left
    icon_size = int(size_h * 0.85)
    icon = create_icon(icon_size)
    icon_y = (size_h - icon_size) // 2
    canvas.paste(icon, (icon_y, icon_y), icon)

    # Draw "Pool Lab" text to the right of the icon
    text = "Pool Lab"
    text_x = icon_size + int(size_w * 0.05)
    text_y = size_h // 2

    # Try to use a reasonable font size
    font_size = int(size_h * 0.35)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_height = bbox[3] - bbox[1]
    draw.text(
        (text_x, text_y - text_height // 2),
        text,
        fill=(*BG_COLOR, 255),
        font=font,
    )

    return canvas


def main() -> None:
    """Generate all brand image variants."""
    BRAND_DIR.mkdir(parents=True, exist_ok=True)

    # Generate icons (square)
    icon_256 = create_icon(256)
    icon_256.save(BRAND_DIR / "icon.png")
    print("  Created icon.png (256x256)")

    icon_512 = create_icon(512)
    icon_512.save(BRAND_DIR / "icon@2x.png")
    print("  Created icon@2x.png (512x512)")

    # Generate logos (rectangular, transparent background)
    logo_256 = create_logo(256, 128)
    logo_256.save(BRAND_DIR / "logo.png")
    print("  Created logo.png (256x128)")

    logo_512 = create_logo(512, 256)
    logo_512.save(BRAND_DIR / "logo@2x.png")
    print("  Created logo@2x.png (512x256)")

    print(f"\nAll brand images saved to: {BRAND_DIR}")


if __name__ == "__main__":
    main()
