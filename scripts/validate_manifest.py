"""Validate manifest.json key ordering and required fields.

Catches the most common hassfest failures locally before pushing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent.parent / "custom_components" / "pool_lab" / "manifest.json"

REQUIRED_KEYS = ["domain", "name", "version"]
REQUIRED_ORDER = ["domain", "name"]  # Must be first two keys


def validate() -> list[str]:
    """Validate manifest.json and return a list of error messages."""
    errors: list[str] = []

    if not MANIFEST_PATH.exists():
        errors.append(f"manifest.json not found at {MANIFEST_PATH}")
        return errors

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    keys = list(manifest.keys())

    # Check required keys exist
    for key in REQUIRED_KEYS:
        if key not in manifest:
            errors.append(f"Missing required key: {key}")

    # Check first two keys are domain, name
    if len(keys) >= 2:
        if keys[0] != "domain":
            errors.append(f"First key must be 'domain', got '{keys[0]}'")
        if keys[1] != "name":
            errors.append(f"Second key must be 'name', got '{keys[1]}'")

    # Check remaining keys are alphabetically sorted
    remaining = keys[2:]
    if remaining != sorted(remaining):
        errors.append(
            f"Keys after 'domain' and 'name' must be alphabetical. "
            f"Got: {remaining}, expected: {sorted(remaining)}"
        )

    # Check version format
    if "version" in manifest:
        parts = manifest["version"].split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            errors.append(f"Version must be semver (X.Y.Z), got: {manifest['version']}")

    return errors


if __name__ == "__main__":
    errors = validate()
    if errors:
        print("manifest.json validation failed:")
        for error in errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    print("manifest.json validation passed ✓")
