#!/usr/bin/env python3
"""OCR a scanned PDF page by page from the page images. Standard library plus the
`pdftoppm` and `tesseract` programs (with the eng and grc language packs).

Resumable: pages that already have an output file are skipped. Each page is written to
OUT/NNNN.txt where NNNN is the PDF page number (not the printed page number).

  python3 ocr_pdf.py book.pdf --out data/raw/bullinger/ocr --lang eng+grc
  python3 ocr_pdf.py book.pdf --out ocr --first 470 --last 480 --time-budget 500
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def pdf_pages(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(next(l.split()[1] for l in out.splitlines() if l.startswith("Pages:")))


def ocr_page(pdf, page, out, dpi, lang, boxes=False):
    dest = out / f"{page:04d}.txt"
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "p"
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-gray", "-png",
                        str(pdf), str(prefix)], check=True, capture_output=True)
        png = next(Path(tmp).glob("p*.png"))
        text = subprocess.run(["tesseract", str(png), "stdout", "-l", lang, "--psm", "1"],
                              check=True, capture_output=True, text=True).stdout
        if boxes:  # word-level boxes: left, top, width, height in pixels at this dpi, plus confidence
            tsv = subprocess.run(["tesseract", str(png), "stdout", "-l", lang, "--psm", "1", "tsv"],
                                 check=True, capture_output=True, text=True).stdout
            (out / f"{page:04d}.tsv").write_text(tsv, encoding="utf-8")
    dest.write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--lang", default="eng+grc")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--boxes", action="store_true",
                    help="also write NNNN.tsv with a bounding box and confidence for every word (slower)")
    ap.add_argument("--time-budget", type=float, default=None,
                    help="stop starting new pages after this many seconds; rerun to continue")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    last = a.last or pdf_pages(a.pdf)
    todo = [p for p in range(a.first, last + 1) if not (out / f"{p:04d}.txt").exists()]
    start = time.time()
    tess = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    (out / "meta.json").write_text(json.dumps(
        {"pdf": Path(a.pdf).name, "dpi": a.dpi, "lang": a.lang, "psm": 1, "tesseract": tess}, indent=1))

    def work(page):
        if a.time_budget and time.time() - start > a.time_budget:
            return None
        ocr_page(a.pdf, page, out, a.dpi, a.lang, a.boxes)
        return page

    done = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(work, todo):
            done += r is not None
    left = len([p for p in range(a.first, last + 1) if not (out / f"{p:04d}.txt").exists()])
    print(f"OCR'd {done} pages in {time.time() - start:.0f}s; {left} of pages {a.first}-{last} still to do")
    sys.exit(0)


if __name__ == "__main__":
    main()
