#!/usr/bin/env python3
"""Render the part of a scanned page that a graph record points to, so a person or a
checker can look at the original after the fact. Needs `pdftoppm`.

  python3 crop.py book.pdf --page 474 --box 906 415 106 42 --dpi 300 --pad 20 --out crop.png

--box is left top width height in pixels at --dpi, exactly as stored in a provenance record.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, required=True, help="PDF page number (not the printed one)")
    ap.add_argument("--box", type=int, nargs=4, metavar=("LEFT", "TOP", "WIDTH", "HEIGHT"), required=True)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--pad", type=int, default=20, help="extra pixels of context around the box")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    left, top, w, h = a.box
    x, y = max(0, left - a.pad), max(0, top - a.pad)
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "c"
        subprocess.run(["pdftoppm", "-f", str(a.page), "-l", str(a.page), "-r", str(a.dpi), "-png",
                        "-x", str(x), "-y", str(y), "-W", str(w + 2 * a.pad), "-H", str(h + 2 * a.pad),
                        a.pdf, str(prefix)], check=True, capture_output=True)
        Path(a.out).write_bytes(next(Path(tmp).glob("c*.png")).read_bytes())
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
