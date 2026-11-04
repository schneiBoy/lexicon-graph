#!/usr/bin/env python3
"""Pre-render scanned pages to small grey WebP images so that looking at the original is a
file read, not a PDF render. Needs `pdftoppm` and Pillow. Resumable.

  python3 prerender.py book.pdf --out pages/bullinger --dpi 200
  python3 prerender.py book.pdf --out pages/bullinger --first 470 --last 480

Writes NNNN.webp (NNNN = PDF page number). A crop for a provenance box is then a slice:

  from prerender import crop_from_page
  crop_from_page("pages/bullinger/0474.webp", box, box_dpi=300, page_dpi=200, pad=20)
"""
import argparse
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image


def render(pdf, page, out, dpi, quality):
    dest = out / f"{page:04d}.webp"
    if dest.exists():
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "p"
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-gray", "-png",
                        str(pdf), str(prefix)], check=True, capture_output=True)
        Image.open(next(Path(tmp).glob("p*.png"))).save(dest, "WEBP", quality=quality)
    return 1


def crop_from_page(webp, box, box_dpi, page_dpi, pad=20):
    """Cut a provenance box (pixels at box_dpi) out of a pre-rendered page (rendered at page_dpi)."""
    k = page_dpi / box_dpi
    left, top, w, h = box
    img = Image.open(webp)
    return img.crop((max(0, int((left - pad) * k)), max(0, int((top - pad) * k)),
                     min(img.width, int((left + w + pad) * k)), min(img.height, int((top + h + pad) * k))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--quality", type=int, default=75)
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    last = a.last or int(next(l.split()[1] for l in subprocess.run(
        ["pdfinfo", a.pdf], capture_output=True, text=True, check=True).stdout.splitlines()
        if l.startswith("Pages:")))
    with ThreadPoolExecutor(a.workers) as ex:
        done = sum(ex.map(lambda p: render(a.pdf, p, out, a.dpi, a.quality), range(a.first, last + 1)))
    size = sum(f.stat().st_size for f in out.glob("*.webp")) / 1e6
    print(f"rendered {done} pages; {out} now holds {size:.1f} MB")


if __name__ == "__main__":
    main()
