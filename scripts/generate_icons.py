"""Generate brand icons from the official Pool Lab logo.

Derives all required Home Assistant brand image variants from the source logo.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).parent
SOURCE_LOGO = SCRIPT_DIR / "source_logo_full.png"
BRAND_DIR = SCRIPT_DIR.parent / "custom_components" / "pool_lab" / "brand"


def create_logo(source: Image.Image, width: int, height: int) -> Image.Image:
    """Create a rectangular logo at the given dimensions.

    Centers the source logo within the target canvas, scaling to fit
    with padding.
    """
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Scale source to fit within canvas with some padding
    padding_x = int(width * 0.08)
    padding_y = int(height * 0.15)
    max_w = width - 2 * padding_x
    max_h = height - 2 * padding_y

    # Maintain aspect ratio
    src_ratio = source.width / source.height
    target_ratio = max_w / max_h

    if src_ratio > target_ratio:
        # Source is wider — fit to width
        new_w = max_w
        new_h = int(max_w / src_ratio)
    else:
        # Source is taller — fit to height
        new_h = max_h
        new_w = int(max_h * src_ratio)

    resized = source.resize((new_w, new_h), Image.LANCZOS)

    # Center on canvas
    x_offset = (width - new_w) // 2
    y_offset = (height - new_h) // 2
    canvas.paste(resized, (x_offset, y_offset), resized)

    return canvas


def create_icon(source: Image.Image, size: int) -> Image.Image:
    """Create a square icon at the given size.

    Centers the source logo within a square canvas.
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Scale source to fit within the square with padding
    padding = int(size * 0.10)
    max_dim = size - 2 * padding

    # Maintain aspect ratio, fit within square
    src_ratio = source.width / source.height
    if src_ratio > 1:
        # Wider than tall — fit to width
        new_w = max_dim
        new_h = int(max_dim / src_ratio)
    else:
        new_h = max_dim
        new_w = int(max_dim * src_ratio)

    resized = source.resize((new_w, new_h), Image.LANCZOS)

    # Center on canvas
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

    # Generate icons (square)
    icon_256 = create_icon(source, 256)
    icon_256.save(BRAND_DIR / "icon.png")
    print("  Created icon.png (256x256)")

    icon_512 = create_icon(source, 512)
    icon_512.save(BRAND_DIR / "icon@2x.png")
    print("  Created icon@2x.png (512x512)")

    # Generate logos (rectangular)
    logo_256 = create_logo(source, 256, 128)
    logo_256.save(BRAND_DIR / "logo.png")
    print("  Created logo.png (256x128)")

    logo_512 = create_logo(source, 512, 256)
    logo_512.save(BRAND_DIR / "logo@2x.png")
    print("  Created logo@2x.png (512x256)")

    print(f"\nAll brand images saved to: {BRAND_DIR}")


if __name__ == "__main__":
    main()
