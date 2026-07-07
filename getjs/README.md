# getjs

A simple Python tool to download JavaScript files from a list of URLs, filtered by Content-Type, provided via standard input.

## Features
- Checks each URL's `Content-Type` header (javascript, or a missing header, both pass) and downloads/saves the ones that pass to disk using their original filename (default mode).
- With `-t`, does that same check but just prints the passing urls instead of downloading them — no files are saved.
- Supports concurrent requests with a `-c` option for speed.
- Silent by default — errors and extra diagnostic info only show up with `-v`/`--verbose`.

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

## Behavior notes

- **Content-Type filtering applies to both modes:** default mode runs the exact same Content-Type check as `-t` before deciding whether to download a url — it's not an unconditional downloader. Urls whose Content-Type doesn't contain `javascript` (and isn't missing) are skipped in both modes.
- **Silent by default:** request/connection errors, and skipped/passed-through urls, are only printed to stderr when `-v` is used.
- **Missing Content-Type header:** if a response has no `Content-Type` header at all (even after falling back from `HEAD` to `GET`), the URL still passes the check — since it can't be ruled out as JavaScript — so it's downloaded (default mode) or printed (`-t` mode). With `-v`, a message notes that no header was present.
- **Filenames when downloading:** the saved filename is taken from the URL's path (query strings are ignored), e.g. `.../v2/cspblocked.js?domain=` is saved as `cspblocked.js`. If a URL has no usable filename in its path, it's saved as `download.js`.
