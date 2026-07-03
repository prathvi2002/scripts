# API Path Permutator

A Python CLI tool designed to build structural, permutated directory paths from one or more lists of single base words.

### Why this tool?
Kiterunner (`kr scan`) is highly optimized for scanning complex API routes, but it expects complete paths in its `.kite` or text wordlists. It **does not** automatically break lines down, combine them, or create variations.

This tool bridges that gap. It takes single keywords (like `api`, `v1`, `users`), breaks them down, and builds every possible nested folder combination. This allows you to generate exhaustive, target-specific lists to feed directly into Kiterunner for deep API discovery.

### Best Use Case
The best use case is: you already know an interesting prefix path, and you permute everything after it (the suffix) at a small depth, using a wordlist of target-specific path words.

---

## Features
* **Directory Permutations**: Generates sequential, non-repeating ordered combinations up to a custom depth.
* **Locked Prefixes & Suffixes**: Force a static path (like `api/v1/`) at the start of every line, and/or a fixed segment (like `/health`) at the end.
* **Selective & Global Repeats**: Allow every word to repeat within a path (`--allow-repeats`), or only specific words (`--repeat-words`), with a configurable cap on how many times a word may repeat (default: 2).
* **Multiple Input Wordlists**: Pass several `-i` files at once; they're merged and deduped automatically.
* **Case-Insensitive Merging**: Optionally collapse words that only differ by case (e.g. `Users` / `users`) into one.
* **Word Sanitization**: Words containing `/`, `\`, or non-printable characters are automatically dropped and reported, so they can't corrupt path structure.
* **Exclude List**: Skip exact, case-sensitive lines you've already covered or don't want, via `--exclude-file`.
* **Dry-Run / Stats Mode**: See exact per-depth and total counts without generating or writing a single line.
* **Random Sampling**: Pull a random subset of N unique valid paths instead of the full combinatorial space — useful when the full space is too large to enumerate.
* **Pre-Flight Size Warning**: Warns and asks for confirmation before generating very large outputs (over 1,000,000 lines), unless `-y` is passed.
* **File Extensions**: Automatically appends multiple file formats (like `.json`, `.bak`) to the end of your generated routes.
* **Flexible Output**: Prints directly to your screen/stdout by default, or writes directly to a file.

---

## Usage

### Options
```text
usage: api_path_permutator.py [-h] -i INPUT [INPUT ...] [-o OUTPUT] [-d DEPTH]
                              [-p PREFIX] [-s SUFFIX]
                              [-e EXTENSION [EXTENSION ...]] [--allow-repeats]
                              [--repeat-words REPEAT_WORDS]
                              [--repeat-words-file REPEAT_WORDS_FILE]
                              [--max-word-repeat MAX_WORD_REPEAT]
                              [--merge-case] [--exclude-file EXCLUDE_FILE]
                              [--dry-run] [--sample N] [-y]

Generate sequential URL/API directory permutations with optional prefixes,
suffixes, and extensions.

options:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Path(s) to input single-word text file(s). Accepts
                        multiple files, merged and deduped.
  -o OUTPUT, --output OUTPUT
                        Path to save the generated permuted wordlist (Prints
                        to screen if omitted)
  -d DEPTH, --depth DEPTH
                        Maximum directory/folder depth (default: 3)
  -p PREFIX, --prefix PREFIX
                        An optional locked prefix path (e.g., 'api/v1') forced
                        at the beginning of every path
  -s SUFFIX, --suffix SUFFIX
                        An optional locked suffix path (e.g., 'health' or
                        'export') forced at the end of every path
  -e EXTENSION [EXTENSION ...], --extension EXTENSION [EXTENSION ...]
                        Optional extension(s) to append to paths (e.g., -e
                        json xml bak)
  --allow-repeats       Allow ANY word to appear more than once within a
                        single path (uses combinations-with-repeats instead of
                        permutations)
  --repeat-words REPEAT_WORDS
                        Comma-separated, case-sensitive list of specific words
                        that are allowed to repeat within a path (e.g.,
                        --repeat-words api,v1). All other words remain non-
                        repeating.
  --repeat-words-file REPEAT_WORDS_FILE
                        Path to a wordlist file (one word per line, case-
                        sensitive) whose words are allowed to repeat within a
                        path. Can be combined with --repeat-words.
  --max-word-repeat MAX_WORD_REPEAT
                        Maximum number of times an eligible (repeat-allowed)
                        word may appear within a single path (default: 2).
                        Only applies when --allow-repeats or --repeat-
                        words/--repeat-words-file is set.
  --merge-case          Treat words that only differ by case (e.g. 'Users' vs
                        'users') as duplicates and merge them
  --exclude-file EXCLUDE_FILE
                        Path to a file of exact, case-sensitive output lines
                        to skip during generation.
  --dry-run             Report exact/estimated counts per depth and in total
                        without writing or printing any generated paths.
  --sample N            Instead of generating the full combinatorial space,
                        randomly sample N unique valid paths.
  -y, --yes             Skip the confirmation prompt for very large output
                        runs
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

**4. Lock both a prefix and a suffix**
```bash
python3 api_path_permutator.py -i words.txt -d 3 -p api/v1 -s health -o final_list.txt
```
Every generated line will start with `api/v1/` and end with `/health`. Words already used in the prefix or suffix (matched case-sensitively) are automatically excluded from the middle so they aren't redundantly re-permuted.

**5. Merge multiple wordlists**
```bash
python3 api_path_permutator.py -i common_words.txt target_specific.txt -d 3 -o combined.txt
```

**6. Allow every word to repeat (capped at 2 by default)**
```bash
python3 api_path_permutator.py -i words.txt -d 4 --allow-repeats -o final_list.txt
```
Produces paths like `api/users/settings/users` — a word can appear more than once, but no more than `--max-word-repeat` times (default 2). Raise or lower the cap as needed:
```bash
python3 api_path_permutator.py -i words.txt -d 5 --allow-repeats --max-word-repeat 3
```

**7. Allow only specific words to repeat**
```bash
python3 api_path_permutator.py -i words.txt -d 3 --repeat-words "api,v1"
```
Only `api` and `v1` (case-sensitive, exact match) may repeat within a path; every other word stays non-repeating. You can also source repeatable words from a file, or combine both:
```bash
python3 api_path_permutator.py -i words.txt -d 3 --repeat-words-file repeatable.txt
python3 api_path_permutator.py -i words.txt -d 3 --repeat-words "api" --repeat-words-file repeatable.txt
```

**8. Merge case-duplicate words**
```bash
python3 api_path_permutator.py -i words.txt -d 3 --merge-case
```
Treats `Users` and `users` as the same word, keeping one representative (preferring the lowercase form) instead of generating separate permutation branches for each casing.

**9. Skip paths you've already covered**
```bash
python3 api_path_permutator.py -i words.txt -d 4 --exclude-file already_scanned.txt
```
Any output line that exactly matches a line in `already_scanned.txt` (case-sensitive) is skipped and the skip count is reported.

**10. Check the numbers before committing to a huge run**
```bash
python3 api_path_permutator.py -i words.txt -d 6 --dry-run
```
Prints the exact per-depth and total line counts without generating or writing anything — useful for tuning `-d`, `--allow-repeats`, or `--max-word-repeat` before running for real.

**11. Sample a random subset instead of the full space**
```bash
python3 api_path_permutator.py -i words.txt -d 6 --allow-repeats --sample 5000 -o sample_wordlist.txt
```
Instead of generating every combination (which can be millions of lines at higher depths), pulls 5,000 random unique valid paths respecting all your other flags (prefix/suffix, repeat rules, exclusions).

**12. Skip the confirmation prompt on large runs**
```bash
python3 api_path_permutator.py -i words.txt -d 6 --allow-repeats -y -o huge_list.txt
```
By default, any run estimated to produce more than 1,000,000 lines will pause and ask `Continue? [y/N]`. Pass `-y` to skip that prompt (recommended for scripting/automation).

---

## Notes on Combinatorics

* Plain permutations (no repeat flags) are capped by word count: you can't generate a depth greater than the number of available words, since each word can only appear once per path. The tool will warn you if `-d` exceeds the word pool size.
* `--allow-repeats` and `--repeat-words` switch the underlying algorithm from non-repeating permutations to repeat-allowed combinations, which grow much faster (`word_count ^ depth` before capping/filtering) — use `--dry-run` first if you're unsure of the scale.
* Any word already consumed by `-p/--prefix` or `-s/--suffix` (exact case match) is automatically removed from the permutation pool so it isn't redundantly regenerated in the middle of the path.

---

## Kiterunner Integration
Once your list is generated, compile it straight into a binary `.kite` file and run your scan:

```bash
# 1. Convert text to Kiterunner binary
kr kb convert final_list.txt wordlist.kite

# 2. Run the API scan using full coverage mode
kr scan https://target.com -w wordlist.kite --kitebuilder-full-scan
```
