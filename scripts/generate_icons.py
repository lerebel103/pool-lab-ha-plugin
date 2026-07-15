"""Generate brand icons for the Pool Lab integration.

Creates all required Home Assistant brand image variants programmatically.
No external artwork is needed — the icon is a simple pool-themed design
(concentric water ripples) generated entirely with Pillow.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).parent
BRAND_DIR = SCRIPT_DIR.parent / "custom_components" / "pool_lab" / "brand"
ROOT_BRAND_DIR = SCRIPT_DIR.parent / "brand"

# Brand colors
BG_COLOR = (0, 119, 182)  # Deep pool blue
RIPPLE_COLOR = (255, 255, 255)  # White ripples


def create_icon(size: int) -> Image.Image:
    """Create a square icon with concentric water ripple arcs.

    Features a rounded-rectangle blue background with three concentric
    arc ripples emanating from a central point, representing pool water.
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

    # Center point (slightly above center for visual balance)
    cx = size // 2
    cy = int(size * 0.45)

    # Draw a small filled circle at the center (the "drop point")
    dot_radius = int(size * 0.04)
    draw.ellipse(
        [cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius],
        fill=(*RIPPLE_COLOR, 240),
    )

    # Draw concentric ripple arcs
    line_width = max(2, int(size * 0.025))
    ripple_radii = [int(size * 0.14), int(size * 0.25), int(size * 0.36)]
    alphas = [220, 170, 120]

    for i, r in enumerate(ripple_radii):
        # Draw arc using line segments for smooth rendering with alpha
        num_segments = 40
        start_angle = 20  # degrees from horizontal
        end_angle = 160
        points = []
        for s in range(num_segments + 1):
            angle_deg = start_angle + (end_angle - start_angle) * s / num_segments
            angle_rad = math.radians(angle_deg)
            px = cx + int(r * math.cos(angle_rad))
            py = cy + int(r * 0.5 * math.sin(angle_rad))
            points.append((px, py))

        if len(points) > 1:
            draw.line(points, fill=(*RIPPLE_COLOR, alphas[i]), width=line_width)

    return canvas


def main() -> None:
    """Generate all brand image variants."""
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    ROOT_BRAND_DIR.mkdir(parents=True, exist_ok=True)

    # Generate icons (square)
    icon_256 = create_icon(256)
    icon_256.save(BRAND_DIR / "icon.png")
    icon_256.save(ROOT_BRAND_DIR / "icon.png")
    print("  Created icon.png (256x256)")

    icon_512 = create_icon(512)
    icon_512.save(BRAND_DIR / "icon@2x.png")
    icon_512.save(ROOT_BRAND_DIR / "icon@2x.png")
    print("  Created icon@2x.png (512x512)")

    # Logos are the same as icons (square, no text)
    logo_128 = create_icon(128)
    logo_128.save(BRAND_DIR / "logo.png")
    logo_128.save(ROOT_BRAND_DIR / "logo.png")
    print("  Created logo.png (128x128)")

    logo_256 = create_icon(256)
    logo_256.save(BRAND_DIR / "logo@2x.png")
    logo_256.save(ROOT_BRAND_DIR / "logo@2x.png")
    print("  Created logo@2x.png (256x256)")

    print(f"\nAll brand images saved to: {BRAND_DIR} and {ROOT_BRAND_DIR}")


if __name__ == "__main__":
    main()
