#!/usr/bin/env python

import struct
import os

vec = os.getenv("VECTOR", 0)

if not vec:

    print('cannot read input vector')
    exit(1)
with open(vec, "rb") as f:

    sample_count = struct.unpack('<i', f.read(4))[0]
    print(f"{sample_count} samples in {vec}")


