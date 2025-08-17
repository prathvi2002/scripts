#!/usr/bin/env python3
import sys
from urllib.parse import urlparse

def is_valid_domain(domain):
    # basic check: must contain at least one dot and no spaces
    return '.' in domain and ' ' not in domain

for line in sys.stdin:
    url = line.strip().strip('"')
    if not url:
        continue

    parsed = urlparse(url if url.startswith(("http://", "https://")) else "http://" + url)
    domain = parsed.netloc

    if is_valid_domain(domain):
        print(domain)

