# API Path Permutator

A Python CLI tool designed to build structural, permutated directory paths from a list of single base words. 

### Why this tool?
Kiterunner (`kr scan`) is highly optimized for scanning complex API routes, but it expects complete paths in its `.kite` or text wordlists. It **does not** automatically break lines down, combine them, or create variations. 

This tool bridges that gap. It takes single keywords (like `api`, `v1`, `users`), breaks them down, and builds every possible nested folder combination. This allows you to generate exhaustive, target-specific lists to feed directly into Kiterunner for deep API discovery.

---

## Features
* **Directory Permutations**: Generates sequential, non-repeating ordered combinations up to a custom depth.
* **Locked Prefixes**: Force a static path (like `api/v1/`) to stay fixed at the beginning of every single generated line.
* **File Extensions**: Automatically appends multiple file formats (like `.json`, `.bak`) to the end of your generated routes.
* **Flexible Output**: Prints directly to your screen/stdout by default, or writes directly to a file.

---

## Usage

### Options
```text
options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the input single-word text file
  -o OUTPUT, --output OUTPUT
                        Path to save the generated permuted wordlist (Prints to screen if omitted)
  -d DEPTH, --depth DEPTH
                        Maximum directory/folder depth (default: 3)
  -p PREFIX, --prefix PREFIX
                        An optional locked prefix path (e.g., 'api/v1') forced at the beginning of every path
  -e EXTENSION [EXTENSION ...], --extension EXTENSION [EXTENSION ...]
                        Optional extension(s) to append to paths (e.g., -e json xml bak)
```

### Examples

**1. Basic Run (Prints to screen, max depth 3)**
```bash
python3 api_path_permutator.py -i words.txt
```

**2. Lock a prefix and save to a file**
```bash
python3 api_path_permutator.py -i words.txt -p api/v1 -o wordlist.txt
```

**3. Combine custom depth, prefix, and multiple extensions**
```bash
python3 api_path_permutator.py -i words.txt -d 4 -p api/Users/ -e json bak -o final_list.txt
```

---

## Kiterunner Integration
Once your list is generated, compile it straight into a binary `.kite` file and run your scan:

```bash
# 1. Convert text to Kiterunner binary
kr kb convert final_list.txt wordlist.kite

# 2. Run the API scan using full coverage mode
kr scan https://target.com -w wordlist.kite --kitebuilder-full-scan
```
