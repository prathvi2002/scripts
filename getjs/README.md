# getjs

A simple Python tool to extract or check JavaScript file URLs from a list of URLs provided via standard input.

## Features
- Extracts `<script src="...">` URLs from HTML pages (default mode).
- Checks each URL's `Content-Type` header and outputs it if it looks like JavaScript (`-t` mode).
- Supports concurrent requests with a `-c` option for speed.
- Silent by default — errors and extra diagnostic info only show up with `-v`/`--verbose`.

## Usage

```
cat <urls.txt> | python3 getjs.py
```

### Increase concurrency (faster):

```
cat <urls.txt> | python3 getjs.py -c 10
```

### Check Content-Type instead of extracting `<script src>` tags:

```
cat <urls.txt> | python3 getjs.py -t
```

### Verbose mode:

```
cat <urls.txt> | python3 getjs.py -t -v
```

## Options

- `-t`, `--check-content-type` — Instead of downloading HTML and extracting `<script src>` tags, request each URL from stdin directly and print it unchanged if its `Content-Type` header partially contains `javascript`.
- `-c N`, `--concurrent N` — Number of concurrent worker threads (default: `1`, sequential). Works with both the default mode and `-t`.
- `-v`, `--verbose` — Print errors and extra diagnostic messages to stderr. By default, request errors are suppressed and nothing extra is printed.

## Behavior notes

- **Silent by default:** request/connection errors are only printed to stderr when `-v` is used. Without `-v`, failed requests are skipped quietly.
- **Missing Content-Type header (`-t` mode only):** if a response has no `Content-Type` header at all (even after falling back from `HEAD` to `GET`), the URL is still output, since it can't be ruled out as JavaScript. When `-v` is also passed, a message is printed noting that no `Content-Type` header was present, which is why that URL is being extracted/output.
