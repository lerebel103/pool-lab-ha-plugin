"""Generate brand icons from the official Pool Lab logo.

Derives all required Home Assistant brand image variants from source images:
- icon.png / icon@2x.png: from source_logo.png (official app icon)
- logo.png / logo@2x.png: from source_logo_full.png (wordmark/logo)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).parent
SOURCE_ICON = SCRIPT_DIR / "source_logo.png"
SOURCE_LOGO = SCRIPT_DIR / "source_logo_full.png"
BRAND_DIR = SCRIPT_DIR.parent / "custom_components" / "pool_lab" / "brand"


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
    """Create a square icon by resizing the official app icon.

    The source icon already has proper branding and background,
    so we just resize it cleanly to the target dimensions.
    """
    return source.resize((size, size), Image.LANCZOS)


def main() -> None:
    """Generate all brand image variants from the source images."""
    if not SOURCE_ICON.exists():
        print(f"Error: Source icon not found at {SOURCE_ICON}")
        print("Place the official Pool Lab app icon at the expected path.")
        return

    if not SOURCE_LOGO.exists():
        print(f"Error: Source logo not found at {SOURCE_LOGO}")
        print("Place the Pool Lab wordmark/logo at the expected path.")
        return

    BRAND_DIR.mkdir(parents=True, exist_ok=True)

    icon_source = Image.open(SOURCE_ICON).convert("RGBA")
    print(f"Source icon: {icon_source.size[0]}x{icon_source.size[1]}")

    logo_source = Image.open(SOURCE_LOGO).convert("RGBA")
    print(f"Source logo: {logo_source.size[0]}x{logo_source.size[1]}")

    # Generate icons (square, resized from official app icon)
    icon_256 = create_icon(icon_source, 256)
    icon_256.save(BRAND_DIR / "icon.png")
    print("  Created icon.png (256x256)")

    icon_512 = create_icon(icon_source, 512)
    icon_512.save(BRAND_DIR / "icon@2x.png")
    print("  Created icon@2x.png (512x512)")

    # Generate logos (rectangular, transparent background)
    logo_256 = create_logo(logo_source, 256, 128)
    logo_256.save(BRAND_DIR / "logo.png")
    print("  Created logo.png (256x128)")

    logo_512 = create_logo(logo_source, 512, 256)
    logo_512.save(BRAND_DIR / "logo@2x.png")
    print("  Created logo@2x.png (512x256)")

    print(f"\nAll brand images saved to: {BRAND_DIR}")


if __name__ == "__main__":
    main()
