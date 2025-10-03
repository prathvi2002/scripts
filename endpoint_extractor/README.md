# Endpoint Extractor

A simple Python script that reads URLs from standard input and outputs only the endpoint (path) portion of each URL.

## Features
- Reads from stdin, making it easy to use with pipes or files.
- Strips query strings, fragments, and other URL parts — outputs only the path.
- Works with both HTTP and HTTPS URLs.

## Usage

`cat <urls.txt> | python3 extract_endpoint.py`
