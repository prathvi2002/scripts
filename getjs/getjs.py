#!/usr/bin/env python3

"""
Reads a list of URLs from piped standard input

Downloads the HTML source of each URL

Extracts all JavaScript file URLs from <script src="..."> tags

Resolves relative paths to full URLs

Prints the final JS URLs to stdout
"""

import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from functools import partial
from concurrent.futures import ThreadPoolExecutor


def extract_js_urls(url, verbose=False):
    js_urls = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        scripts = soup.find_all('script', src=True)
        for tag in scripts:
            full_url = urljoin(url, tag['src'])
            js_urls.append(full_url)
    except Exception as e:
        if verbose:
            print(f"[ERROR] {url} - {e}", file=sys.stderr)
    return js_urls


def is_javascript_content_type(url, verbose=False):
    """
    Checks the Content-Type header of a URL (unmodified, as-is).
    Returns the url itself if the header partially contains 'javascript'
    (case-insensitive), otherwise returns None.

    If no Content-Type header is present at all (even after falling back
    to a GET request), the url is still returned, since we can't rule it
    out as JavaScript. When verbose mode is on, a message is printed
    noting that the header was missing and that's why the url is being
    extracted/output.
    """
    try:
        # Try a HEAD request first (cheaper), fall back to GET if HEAD
        # doesn't give us a usable Content-Type or isn't supported.
        resp = requests.head(url, timeout=10, allow_redirects=True)
        content_type = resp.headers.get('Content-Type', '')

        if not content_type:
            resp = requests.get(url, timeout=10, stream=True)
            content_type = resp.headers.get('Content-Type', '')
            resp.close()

        if 'javascript' in content_type.lower():
            return url

        if not content_type:
            if verbose:
                print(
                    f"[INFO] {url} - no Content-Type header was present, "
                    f"so extracting/outputting this url anyway",
                    file=sys.stderr
                )
            return url
    except Exception as e:
        if verbose:
            print(f"[ERROR] {url} - {e}", file=sys.stderr)
    return None


def run_extract_mode(urls, concurrent, verbose):
    worker = partial(extract_js_urls, verbose=verbose)
    if concurrent and concurrent > 1:
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            for js_files in executor.map(worker, urls):
                for js in js_files:
                    print(js)
                    print("")
    else:
        for url in urls:
            js_files = worker(url)
            for js in js_files:
                print(js)
                print("")


def run_content_type_mode(urls, concurrent, verbose):
    worker = partial(is_javascript_content_type, verbose=verbose)
    if concurrent and concurrent > 1:
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            for result in executor.map(worker, urls):
                if result:
                    print(result)
    else:
        for url in urls:
            result = worker(url)
            if result:
                print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reads URLs from stdin. Default mode: downloads HTML "
                     "and extracts JS file URLs from <script src=...> tags."
    )
    parser.add_argument(
        "-t", "--check-content-type",
        action="store_true",
        help="Instead of extracting <script src> tags, request each URL "
             "from stdin directly and print it unchanged if its "
             "Content-Type header partially contains 'javascript' (or if "
             "no Content-Type header is present at all)."
    )
    parser.add_argument(
        "-c", "--concurrent",
        type=int,
        default=1,
        metavar="N",
        help="Number of concurrent worker threads to use (default: 1, "
             "i.e. sequential). Works with both the default mode and "
             "--check-content-type."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print errors and extra info (e.g. requests that fail, or "
             "urls output because no Content-Type header was present) to "
             "stderr. Silent by default."
    )
    args = parser.parse_args()

    urls = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        urls.append(line)

    if args.check_content_type:
        run_content_type_mode(urls, args.concurrent, args.verbose)
    else:
        run_extract_mode(urls, args.concurrent, args.verbose)
