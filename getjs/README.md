# getjs

A simple Python script to download multiple JavaScript files concurrently from a list of URLs provided via standard input.

## Features
- Downloads `.js` files from a list of URLs.
- Saves each file using its original filename.
- Supports concurrent downloads with a `-c` option for speed.

## Usage

`cat <js-urls.txt> | python3 getjs.py`

### Increase concurrency (faster):
`cat <js-urls.txt> | python3 getjs.py -c <10>`
