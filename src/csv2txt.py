#!/usr/bin/env python

import csv
import os

annotate_csv = os.getenv("ANNOTATE_CSV", False)
annotate_txt = os.getenv("ANNOTATE_TXT", False)
positives = os.getenv("POSITIVES", False)

if not annotate_csv or not annotate_txt or not positives:

    print("csv2txt: verify environment variables")
    exit(1)

with open(annotate_csv, newline = '') as csvfile, open(annotate_txt, 'w') as txtfile:

    reader = csv.DictReader(csvfile)
    for row in reader:

        filename = row['filename']
        x, y, w, h = row['x'], row['y'], row['width'], row['height']
        txtfile.write(f"{positives}/{filename} 1 {x} {y} {w} {h}\n")
print(f"{annotate_csv} converted to {annotate_txt}")
exit(0)
