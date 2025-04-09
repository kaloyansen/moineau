#!/usr/bin/env python

import os

annotate_txt = os.getenv("ANNOTATE_TXT", False)
base_path = os.getenv("DATASET", False)

missing = []

with open(annotate_txt, "r") as f:

    for line in f:

        line = line.strip()
        if not line: continue
        image_rel_path = line.split()[0]
        image_path = os.path.join(base_path, image_rel_path)
        print(image_path)
        if not os.path.isfile(image_path):

            missing.append(image_path)
if missing:

    print("warning: missing images")
    for path in missing: print("  -", path)
else:

    print("all annotated image files exist")
