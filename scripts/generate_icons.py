"""Generate brand icons from the official Pool Lab logo.

Derives all required Home Assistant brand image variants from the source logo.
Icons get a rounded background for visibility in the HA UI.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).parent
SOURCE_LOGO = SCRIPT_DIR / "source_logo_full.png"
BRAND_DIR = SCRIPT_DIR.parent / "custom_components" / "pool_lab" / "brand"

# Pool Lab brand blue
BRAND_COLOR = (0, 119, 182)


def create_logo(source: Image.Image, width: int, height: int) -> Image.Image:
    """Create a rectangular logo at the given dimensions.

    Centers the source logo within the target canvas, scaling to fit.
    """
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    padding_x = int(width * 0.08)
    padding_y = int(height * 0.15)
    max_w = width - 2 * padding_x
    max_h = height - 2 * padding_y

    src_ratio = source.width / source.height
    target_ratio = max_w / max_h

    if src_ratio > target_ratio:
        new_w = max_w
        new_h = int(max_w / src_ratio)
    else:
        new_h = max_h
        new_w = int(max_h * src_ratio)

    resized = source.resize((new_w, new_h), Image.LANCZOS)

    x_offset = (width - new_w) // 2
    y_offset = (height - new_h) // 2
    canvas.paste(resized, (x_offset, y_offset), resized)

    return canvas


def create_icon(source: Image.Image, size: int) -> Image.Image:
    """Create a square icon with a rounded-rectangle background.

    Places the logo on a solid brand-colored background so it's
    clearly visible in the HA integration list.
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Draw rounded rectangle background
    radius = int(size * 0.18)
    margin = int(size * 0.02)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(*BRAND_COLOR, 255),
    )

    # Scale and center the logo on the background
    padding = int(size * 0.15)
    max_w = size - 2 * padding
    max_h = size - 2 * padding

    src_ratio = source.width / source.height
    if src_ratio > 1:
        new_w = max_w
        new_h = int(max_w / src_ratio)
    else:
        new_h = max_h
        new_w = int(max_h * src_ratio)

    resized = source.resize((new_w, new_h), Image.LANCZOS)

    x_offset = (size - new_w) // 2
    y_offset = (size - new_h) // 2
    canvas.paste(resized, (x_offset, y_offset), resized)

    return canvas


def main() -> None:
    """Generate all brand image variants from the source logo."""
    if not SOURCE_LOGO.exists():
        print(f"Error: Source logo not found at {SOURCE_LOGO}")
        print("Download it first or place it at the expected path.")
        return

    BRAND_DIR.mkdir(parents=True, exist_ok=True)

    source = Image.open(SOURCE_LOGO).convert("RGBA")
    print(f"Source logo: {source.size[0]}x{source.size[1]}")

    # Generate icons (square with background)
    icon_256 = create_icon(source, 256)
    icon_256.save(BRAND_DIR / "icon.png")
    print("  Created icon.png (256x256)")

    icon_512 = create_icon(source, 512)
    icon_512.save(BRAND_DIR / "icon@2x.png")
    print("  Created icon@2x.png (512x512)")

    # Generate logos (rectangular, transparent background)
    logo_256 = create_logo(source, 256, 128)
    logo_256.save(BRAND_DIR / "logo.png")
    print("  Created logo.png (256x128)")

    logo_512 = create_logo(source, 512, 256)
    logo_512.save(BRAND_DIR / "logo@2x.png")
    print("  Created logo@2x.png (512x256)")

    print(f"\nAll brand images saved to: {BRAND_DIR}")


if __name__ == "__main__":
    main()
