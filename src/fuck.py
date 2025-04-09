#!/usr/bin/env python

import os
from collections import defaultdict

annotate_txt = os.getenv("ANNOTATE_TXT", False)
annotations = defaultdict(list)
with open(annotate_txt) as f:
    for line in f:
        parts = line.strip().split()
        filename = parts[0]
        box = tuple(map(int, parts[2:]))  # x, y, w, h
        annotations[filename].append(box)

with open(f"{annotate_txt}.new", 'w') as f:
    for filename, boxes in annotations.items():
        line = f"{filename} {len(boxes)}"
        for (x, y, w, h) in boxes:
            line += f" {x} {y} {w} {h}"
        f.write(line + "\n")
