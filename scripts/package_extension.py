"""Build the installable Clone Fields Blender extension zip."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"
ZIP_PATH = DIST_DIR / "clone_fields.zip"

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    "dist",
}
EXCLUDED_NAMES = {
    ".DS_Store",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
}


def should_include(path: Path) -> bool:
    relative = path.relative_to(REPO_ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def main() -> None:
    DIST_DIR.mkdir(exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(REPO_ROOT.rglob("*")):
            if should_include(path):
                archive.write(path, path.relative_to(REPO_ROOT))

    desktop_zip = Path.home() / "Desktop" / "clone_fields.zip"
    if desktop_zip.parent.exists():
        shutil.copy2(ZIP_PATH, desktop_zip)

    print(ZIP_PATH)


if __name__ == "__main__":
    main()

