"""Build the installable Clone Fields Blender extension zip."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"
ZIP_PATH = DIST_DIR / "clone_fields.zip"
NODE_LIBRARY_PATH = REPO_ROOT / "geometry_nodes" / "assets" / "clone_fields_nodes.blend"

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    "dist",
}
EXCLUDED_NAMES = {
    ".DS_Store",
}
EXCLUDED_SUFFIXES = {
    ".avif",
    ".gif",
    ".jpeg",
    ".jpg",
    ".pyc",
    ".png",
    ".webp",
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


def find_blender() -> Path:
    configured = os.environ.get("BLENDER_BIN")
    if configured:
        return Path(configured).expanduser()

    discovered = shutil.which("blender")
    if discovered:
        return Path(discovered)

    mac_binary = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if mac_binary.is_file():
        return mac_binary

    raise RuntimeError(
        "Blender was not found. Set BLENDER_BIN or use --skip-node-library."
    )


def build_node_library() -> None:
    blender = find_blender()
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        "--python",
        str(REPO_ROOT / "scripts" / "build_node_library.py"),
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)
    if not NODE_LIBRARY_PATH.is_file():
        raise RuntimeError(f"Node library was not created: {NODE_LIBRARY_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-node-library",
        action="store_true",
        help="Package the existing generated node library without rebuilding it",
    )
    parser.add_argument(
        "--no-desktop-copy",
        action="store_true",
        help="Do not copy the finished zip to the Desktop",
    )
    args = parser.parse_args()

    if not args.skip_node_library:
        build_node_library()

    DIST_DIR.mkdir(exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(REPO_ROOT.rglob("*")):
            if should_include(path):
                archive.write(path, path.relative_to(REPO_ROOT))

    desktop_zip = Path.home() / "Desktop" / "clone_fields.zip"
    if not args.no_desktop_copy and desktop_zip.parent.exists():
        shutil.copy2(ZIP_PATH, desktop_zip)

    print(ZIP_PATH)


if __name__ == "__main__":
    main()
