#!/usr/bin/env python3

import sys
import os
import argparse
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"
}

def safe_filename_from_url(url):
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename:
        # fallback: use hash of URL
        filename = hashlib.md5(url.encode()).hexdigest() + ".js"
    return filename

def download_js(url):
    url = url.strip()
    if not url:
        return None
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        filename = safe_filename_from_url(url)
        with open(filename, "wb") as f:
            f.write(response.content)
        return f"[+] Saved: {filename}"
    except requests.exceptions.RequestException as e:
        return f"[-] Failed: {url} ({e})"

def main():
    parser = argparse.ArgumentParser(description="Download JS files concurrently from stdin URLs.")
    parser.add_argument("-c", "--concurrent", type=int, default=5, help="Number of concurrent downloads (default: 5)")
    args = parser.parse_args()

    if sys.stdin.isatty():
        print("Usage: cat urls.txt | python3 getjs.py [-c 10]")
        sys.exit(1)

    urls = [line.strip() for line in sys.stdin if line.strip()]
    if not urls:
        print("[-] No URLs provided.")
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=args.concurrent) as executor:
        future_to_url = {executor.submit(download_js, url): url for url in urls}
        for future in as_completed(future_to_url):
            result = future.result()
            if result:
                print(result)

if __name__ == "__main__":
    main()

