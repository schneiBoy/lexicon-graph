#!/usr/bin/env python3
"""Cut the page-image strip behind a range of OCR lines, so each line can be proofread against the scan.

  BULLINGER_PDF=scan.pdf python3 proof_crop.py LINES_DIR PAGE COLUMN FIRST_LINE LAST_LINE OUT.png

Prints the OCR text of those lines, numbered, to compare with the image.
"""
import json, os, subprocess, sys
from pathlib import Path
d, page, col, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
meta = json.load(open(Path(d) / f"{page:04d}_lines.json"))
lines = meta['columns'][col][a:b + 1]
dpi = meta['dpi']
l = min(x['box'][0] for x in lines) - 12
t = min(x['box'][1] for x in lines) - 10
r = max(x['box'][0] + x['box'][2] for x in lines) + 12
bt = max(x['box'][1] + x['box'][3] for x in lines) + 10
subprocess.run(['pdftoppm', '-r', str(dpi), '-gray', '-f', str(page), '-l', str(page), '-x', str(max(0, l)), '-y', str(max(0, t)),
                '-W', str(r - l), '-H', str(bt - t), '-png', '-singlefile', os.environ['BULLINGER_PDF'], out[:-4]], check=True)
for i, x in enumerate(lines, a):
    print(f"{i:3d} | {x['text']}")
