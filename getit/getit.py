#!/home/ishu/dev/scripts/venv_scripts/bin/python3

import requests
import shutil
import argparse
import argcomplete
import sys
import concurrent.futures
import urllib3
import json

from bs4 import BeautifulSoup
from pygments import highlight
from pygments.lexers import HtmlLexer
from pygments.formatters import TerminalFormatter

# Disable SSL certificate warnings 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

terminal_width = shutil.get_terminal_size().columns

YELLOW = "\033[93m"
GRAY = "\033[90m"
GREEN = "\033[32m"
CYAN = "\033[96m"
PINK = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"


def make_request(url, headers, timeout=10, proxy_url=None, follow_redirects=False):
    try:
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, timeout=timeout, proxies=proxies, verify=False, allow_redirects=follow_redirects, headers=headers)

        if response.status_code == 429:
            print(f"{RED}[~] Response code: {response.status_code}. Probably rate limited.{RESET} For URL: {url}")
        # commented the below line coz Request without raise_for_status to allow 4xx/5xx body inspection to see if modified parameter value is present in response body or not.
        # response.raise_for_status()  # raises error for bad responses (4xx, 5xx).
    # Handles all request failures
    except Exception as e:
        print(f"{YELLOW}[!] Request failed for {url}: {e}{RESET}")
        response = None

    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple script to make HTTP GET request to proivded URLs and prints the response.", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more target URLs to test. Provide as CLI positional arguments or via piped stdin. Example: hsqli http://example.com?id=1 OR echo \"http://example.com?id=1\" | hsqli"
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=10,
        help="Maximum seconds to wait for a response (default 10). Example: --timeout 10"
    )
    parser.add_argument(
        "-T",
        "--threads",
        type=int,
        default=10,
        help="Number of concurrent worker threads to use (default: 1). Example: --threads 20"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        default=None,
        help="Optional proxy URL to route requests through. Example: --proxy http://127.0.0.1:9090"
    )
    parser.add_argument(
        "-f",
        "--follow-redirects",
        action="store_true",
        help="Follow redirects (default: False). Example: --follow-redirects"
    )
    parser.add_argument(
        "-H", "--header",
        action="append",
        help="Additional HTTP headers to include in requests, in 'Key: Value' format. Can be used multiple times."
    )
    parser.add_argument(
        "-P", "--no-prettify",
        action="store_false",
        dest="prettify",
        default=True,
        help="Disable pretty-printing and syntax highlighting of HTML response bodies (enabled by default)."
    )
    parser.add_argument(
        "-o",
        "--json-output",
        metavar="FILE",
        help="Write the output as JSON to the specified file instead of printing to stdout. Overwrites if the specified file already exists."
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    json_output_value = args.json_output

    timeout_value = args.timeout
    threads_value = args.threads
    proxy_value = args.proxy
    follow_redirects_value = args.follow_redirects

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Accept": "*/*",
        "Accept-Language": "en;q=0.5, *;q=0.1",
        "Accept-Encoding": "gzip, deflate, br"
    }

    if args.header:
        for h in args.header:
            if ":" not in h:
                parser.error(f"Invalid header format: {h}. Use 'Key: Value'")
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    ## Collect URLs from CLI and from stdin if piped
    # Start with any URLs provided as positional arguments from CLI
    urls_value = list(args.urls)
    # If stdin is not a TTY, it means data was piped in
    if not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line:
                urls_value.append(line)

    if not urls_value:
        parser.error("No URLs provided (via args or piped input).")

    # for url in urls_value:
    #     make_request(url=url, headers=headers, timeout=timeout_value, proxy_url=proxy_value, follow_redirects=follow_redirects_value)

    results = []

    MAX_PARALLEL = threads_value

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as executor:
        futures = [
            executor.submit(
                make_request,
                url,
                headers,
                args.timeout,
                args.proxy,
                args.follow_redirects
            )
            for url in urls_value
        ]
    for future in concurrent.futures.as_completed(futures):
        response = future.result()
        if response is not None:
            body = response.text  # Use response.text directly for decoded content
            content_type = response.headers.get("Content-Type", "").lower()

            if "html" in content_type:
                # Prettify HTML for structure
                soup = BeautifulSoup(body, "html.parser")
                pretty_html = soup.prettify()
            else:
                soup = None
                pretty_html = body  # keep as is

            data = {
                "url": response.url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                # "title": soup.title.string.strip() if soup.title else None,
                "title": soup.title.string.strip() if soup and soup.title else None,
                "body": body
            }

            if json_output_value:
                results.append(data)
            else:
                print(f"\n{CYAN}URL:{RESET} {response.url}\n")
                print(f"{GREEN}Status:{RESET} {response.status_code}\n")
                if soup and soup.title:
                    print(f"{GRAY}Title:{RESET} {soup.title.string.strip()}\n")
                else:
                    print("Title: None\n")
                print(f"{YELLOW}Headers:{RESET}\n")
                for k, v in response.headers.items():
                    print(f"  {GRAY}{k}:{RESET} {v}")

                print(f"\n{PINK}Response Body:{RESET}\n")
                # if args.prettify and body and "html" in content_type:
                if args.prettify and soup:
                    highlighted_response_body = highlight(pretty_html, HtmlLexer(), TerminalFormatter())
                    print(highlighted_response_body)
                elif body:
                    print(body)
                else:
                    print(response.text)  # fallback
                print(f"{GRAY}{'─' * terminal_width}{RESET}")
        else:
            print(f"{YELLOW}[!] No response received.{RESET}")
    
    if json_output_value:
        with open(json_output_value, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)