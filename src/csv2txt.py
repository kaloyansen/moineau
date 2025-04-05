#!/usr/bin/env python

import csv
import os

output_csv = os.getenv("OUTPUT_CSV")
output_txt = os.getenv("OUTPUT_TXT")

with open(output_csv, newline = '') as csvfile, open(output_txt, 'w') as out:

    reader = csv.DictReader(csvfile)
    for row in reader:

        filename = row['filename']
        x, y, w, h = row['x'], row['y'], row['width'], row['height']
        out.write(f"positives/{filename} 1 {x} {y} {w} {h}\n")
print(f"{output_csv} converted to {output_txt}")
exit(0)
