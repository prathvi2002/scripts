# getjs

A simple Python tool to download JavaScript files from a list of URLs, filtered by Content-Type, provided via standard input.

## Features
- Checks each URL's `Content-Type` header (javascript, or a missing header, both pass) and downloads/saves the ones that pass to disk using their original filename (default mode).
- With `-t`, does that same check but just prints the passing urls instead of downloading them — no files are saved.
- Supports concurrent requests with a `-c` option for speed.
- Silent by default — errors and extra diagnostic info only show up with `-v`/`--verbose`.
- Supports routing requests through an HTTP/HTTPS proxy (`-p`) or through Tor (`--tor`).

## Usage

Download the JS-looking urls from a list to the current directory:
```
cat <urls.txt> | python3 getjs.py
```

### Save to a specific directory:

```
cat <urls.txt> | python3 getjs.py -o downloaded_js
```

### Increase concurrency (faster):

```
cat <urls.txt> | python3 getjs.py -c 10 -o downloaded_js
```

### Just print the urls that pass the Content-Type check, without downloading:

```
cat <urls.txt> | python3 getjs.py -t
```

### Verbose mode:

```
cat <urls.txt> | python3 getjs.py -v
```

### Route through a proxy (e.g. Burp):

```
cat <urls.txt> | python3 getjs.py -p http://127.0.0.1:8080
```

### Route through Tor:

```
cat <urls.txt> | python3 getjs.py --tor
```

## A typical pipeline

```
cat urls.txt | python3 getjs.py -t -c 10 > js_urls.txt   # 1. preview which urls would pass the check
cat js_urls.txt | python3 getjs.py -c 10 -o downloaded_js  # 2. download those urls (re-checked, then saved)
```

## Options

- `-t`, `--check-content-type` — Instead of downloading and saving files, just print each url unchanged if its `Content-Type` header partially contains `javascript` (or is missing entirely — see below).
- `-c N`, `--concurrent N` — Number of concurrent worker threads (default: `1`, sequential). Works in both modes.
- `-o DIR`, `--output-dir DIR` — Directory to save downloaded files into (default: current directory). Created automatically if it doesn't exist. Only used in the default (download) mode.
- `-v`, `--verbose` — Print errors and extra diagnostic messages to stderr. By default, request errors are suppressed and nothing extra is printed.
- `-p URL`, `--proxy URL` — HTTP/HTTPS proxy URL to route requests through (e.g. `http://127.0.0.1:8080`). Certificate verification is skipped, so intercepting proxies like Burp work out of the box.
- `--tor` — Route requests through the local Tor SOCKS5 proxy at `127.0.0.1:9050`. Takes priority over `-p`/`--proxy` if both are set (a notice is printed to stderr if both are set).
- `--timeout SECONDS` — Timeout in seconds applied to every request (default: `10`). Pass `0` to wait indefinitely (no timeout).

## Behavior notes

- **Content-Type filtering applies to both modes:** default mode runs the exact same Content-Type check as `-t` before deciding whether to download a url — it's not an unconditional downloader. Urls whose Content-Type doesn't contain `javascript` (and isn't missing) are skipped in both modes.
- **Silent by default:** request/connection errors, and skipped/passed-through urls, are only printed to stderr when `-v` is used.
- **Missing Content-Type header:** if a response has no `Content-Type` header at all (even after falling back from `HEAD` to `GET`), the URL still passes the check — since it can't be ruled out as JavaScript — so it's downloaded (default mode) or printed (`-t` mode). With `-v`, a message notes that no header was present.
- **Filenames when downloading:** the saved filename is taken from the URL's path (query strings are ignored), e.g. `.../v2/cspblocked.js?domain=` is saved as `cspblocked.js`. If a URL has no usable filename in its path, it's saved as `download.js`.
- **Timeout:** applies to every HEAD/GET request in both modes. Default is 10 seconds; `--timeout 0` disables the timeout entirely, so a hung connection (common over Tor) will block that request indefinitely instead of erroring out.
- **Proxy vs Tor:** `--tor` and `-p`/`--proxy` both apply to all requests in either mode. If both are set, `--tor` wins and a notice is printed to stderr regardless of `-v`. Using `-p`/`--proxy` disables TLS certificate verification (so intercepting proxies like Burp work without extra setup); `--tor` does not disable verification. Routing through Tor requires the `PySocks` dependency (`pip install requests[socks]`) and a local Tor instance listening on `127.0.0.1:9050`.
