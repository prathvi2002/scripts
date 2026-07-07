#!/usr/bin/env python3

"""
Reads a list of URLs from piped standard input

Default mode: checks each URL's Content-Type header (javascript, or
missing header, both pass) and downloads/saves the ones that pass to
disk using their original filename.

With -t/--check-content-type: instead of downloading and saving,
just prints the url unchanged if it passes that same check.
"""

import os
import sys
import argparse
import requests
from urllib.parse import urlparse
from functools import partial
from concurrent.futures import ThreadPoolExecutor


def is_javascript_content_type(url, verbose=False):
    """
    Checks the Content-Type header of a URL (unmodified, as-is).
    Returns the url itself if the header partially contains 'javascript'
    (case-insensitive), otherwise returns None.

    If no Content-Type header is present at all (even after falling back
    to a GET request), the url is still returned, since we can't rule it
    out as JavaScript. When verbose mode is on, a message is printed
    noting that the header was missing and that's why the url is being
    output.
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
                    f"so outputting this url anyway",
                    file=sys.stderr
                )
            return url

        if verbose:
            print(
                f"[INFO] {url} - skipped, Content-Type is '{content_type}', "
                f"not javascript",
                file=sys.stderr
            )
    except Exception as e:
        if verbose:
            print(f"[ERROR] {url} - {e}", file=sys.stderr)
    return None


def filename_from_url(url):
    """
    Derives a local filename from a url's path (ignoring query string
    and fragment). Falls back to a generic name if the path has nothing
    usable (e.g. a bare domain or trailing slash).
    """
    path = urlparse(url).path
    name = os.path.basename(path)
    return name if name else "download.js"


def download_js_file(url, verbose=False, outdir="."):
    """
    Downloads the given url and saves it to outdir using its original
    filename (derived from the url path). Returns the saved file path
    on success, or None on failure.
    """
    try:
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()
        filename = filename_from_url(url)
        filepath = os.path.join(outdir, filename)
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return filepath
    except Exception as e:
        if verbose:
            print(f"[ERROR] {url} - {e}", file=sys.stderr)
    return None


def check_and_download(url, verbose=False, outdir="."):
    """
    Checks the url's Content-Type the same way -t does (javascript, or
    missing header, both pass; anything else is skipped) and only
    downloads/saves it if it passes.
    """
    target_url = is_javascript_content_type(url, verbose)
    if not target_url:
        return None
    return download_js_file(target_url, verbose, outdir)


def run_download_mode(urls, concurrent, verbose, outdir):
    if outdir != "." and not os.path.isdir(outdir):
        os.makedirs(outdir, exist_ok=True)

    worker = partial(check_and_download, verbose=verbose, outdir=outdir)
    if concurrent and concurrent > 1:
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            for filepath in executor.map(worker, urls):
                if filepath:
                    print(filepath)
    else:
        for url in urls:
            filepath = worker(url)
            if filepath:
                print(filepath)


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
        description="Reads URLs from stdin. Default mode: checks each url's "
                     "Content-Type (like -t does), then downloads/saves the "
                     "ones that pass to disk using their original filename."
    )
    parser.add_argument(
        "-t", "--check-content-type",
        action="store_true",
        help="Instead of downloading and saving files, just print each url "
             "unchanged if its Content-Type header partially contains "
             "'javascript' (or if no Content-Type header is present at all)."
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
        "-o", "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory to save downloaded files into (default: current "
             "directory). Created if it doesn't exist. Only used in the "
             "default (download) mode."
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
        run_download_mode(urls, args.concurrent, args.verbose, args.output_dir)
