#!/usr/bin/python3

import sys
from urllib.parse import urlparse

for line in sys.stdin:
    url = line.strip()
    if not url:
        continue
    parsed = urlparse(url)
    print(parsed.path)

