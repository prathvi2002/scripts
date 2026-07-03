import itertools
import argparse
import sys
import os
import math
import random
from collections import Counter


def read_wordlist(input_files):
    """Read one or more wordlist files, merge, strip blank lines, and dedupe."""
    raw_words = []
    for path in input_files:
        if not os.path.exists(path):
            print(f"[-] Error: Input file '{path}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            raw_words.extend(line.strip() for line in f if line.strip())
    return raw_words


def sanitize_words(raw_words):
    """
    Drop words that would corrupt path structure (slashes, backslashes,
    non-printable/control characters). Returns (clean_words, rejected_words).
    """
    clean = []
    rejected = []
    for w in raw_words:
        if "/" in w or "\\" in w or not w.isprintable():
            rejected.append(w)
        else:
            clean.append(w)
    return clean, rejected


def merge_case_insensitive(words):
    """
    Collapse words that only differ by case into a single representative
    (prefers an all-lowercase variant if one exists, otherwise the
    alphabetically-first variant). Returns (merged_words, dropped_words).
    """
    groups = {}
    for w in words:
        groups.setdefault(w.lower(), []).append(w)

    merged = []
    dropped = []
    for key, variants in groups.items():
        if len(variants) > 1:
            chosen = key if key in variants else sorted(variants)[0]
            merged.append(chosen)
            dropped.extend(sorted(v for v in variants if v != chosen))
        else:
            merged.append(variants[0])
    return sorted(merged), sorted(dropped)


def load_repeat_words(repeat_words_csv, repeat_words_file):
    """
    Build the case-sensitive set of words allowed to repeat within a single
    path, sourced from a comma-separated CLI string and/or a wordlist file.
    """
    repeat_set = set()

    if repeat_words_csv:
        repeat_set |= set(w.strip() for w in repeat_words_csv.split(",") if w.strip())

    if repeat_words_file:
        if not os.path.exists(repeat_words_file):
            print(f"[-] Error: Repeat-words file '{repeat_words_file}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(repeat_words_file, 'r', encoding='utf-8') as f:
            repeat_set |= set(line.strip() for line in f if line.strip())

    return repeat_set


def load_exclude_set(exclude_file):
    """Load exact (case-sensitive) output lines to skip during generation."""
    if not exclude_file:
        return set()
    if not os.path.exists(exclude_file):
        print(f"[-] Error: Exclude file '{exclude_file}' not found.", file=sys.stderr)
        sys.exit(1)
    with open(exclude_file, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def is_valid_combo(combo, repeatable_set, max_repeat):
    """
    True if every word in combo respects the repeat rules:
    - Words in repeatable_set may appear up to max_repeat times.
    - All other words may appear at most once.
    - If repeatable_set is empty, no word may repeat at all.
    """
    if not repeatable_set:
        return len(set(combo)) == len(combo)
    counts = Counter(combo)
    for word, cnt in counts.items():
        limit = max_repeat if word in repeatable_set else 1
        if cnt > limit:
            return False
    return True


def estimate_total(word_count, max_depth, repeats_active, extension_count):
    """
    Estimate total output lines before generating, to warn on huge runs.
    This is an UPPER BOUND when repeats/caps/exclusions are involved, since
    those can only reduce the actual count below the naive product formula.
    """
    per_path_multiplier = 1 + extension_count
    total = 0
    for depth in range(1, max_depth + 1):
        if repeats_active:
            count = word_count ** depth
        else:
            count = math.perm(word_count, depth) if depth <= word_count else 0
        total += count * per_path_multiplier
    return total


def build_lines(combo, clean_prefix, clean_suffix, extensions):
    """Given a word tuple, build the base path plus any extension variants."""
    base_path = "/".join(combo)
    full_path = f"{clean_prefix}{base_path}{clean_suffix}"
    lines = [full_path]
    if extensions:
        for ext in extensions:
            clean_ext = ext if ext.startswith(".") else f".{ext}"
            lines.append(f"{full_path}{clean_ext}")
    return lines


def generate_api_paths(input_files, output_file, max_depth, prefix, suffix,
                        extensions, allow_repeats, merge_case, assume_yes,
                        repeat_words_csv=None, repeat_words_file=None,
                        max_word_repeat=2, exclude_file=None,
                        dry_run=False, sample_n=None,
                        confirm_threshold=1_000_000):
    """
    Reads one or more single-word wordlists, builds sequential directory
    permutations (or repeat-allowed combinations), applies optional locked
    prefix/suffix segments, exclusions, and trailing extensions, and outputs
    them (or reports stats / a random sample, depending on mode).
    """
    raw_words = read_wordlist(input_files)
    words, rejected = sanitize_words(raw_words)
    words = sorted(set(words))

    print(f"[+] Loaded {len(words)} unique base words from {input_files}.", file=sys.stderr)
    if rejected:
        print(f"[!] Skipped {len(rejected)} invalid word(s) containing '/', '\\', or "
              f"non-printable characters: {sorted(set(rejected))}", file=sys.stderr)

    if merge_case:
        words, dropped = merge_case_insensitive(words)
        if dropped:
            print(f"[+] Merged case-insensitive duplicates, dropping: {dropped}", file=sys.stderr)
            print(f"[+] {len(words)} word(s) remain after case merging.", file=sys.stderr)

    # Selective repeat set: only these exact (case-sensitive) words may repeat
    repeat_set = load_repeat_words(repeat_words_csv, repeat_words_file)
    if repeat_set:
        if allow_repeats:
            print(f"[!] --allow-repeats already permits every word to repeat; "
                  f"--repeat-words/--repeat-words-file has no additional effect.", file=sys.stderr)
        else:
            missing = sorted(w for w in repeat_set if w not in words)
            if missing:
                print(f"[!] Repeat word(s) not found in the loaded wordlist and will have no "
                      f"effect: {missing}", file=sys.stderr)
            active = sorted(w for w in repeat_set if w in words)
            if active:
                print(f"[+] Allowing only these word(s) to repeat within a path (case-sensitive): {active}", file=sys.stderr)

    # Format prefix/suffix if provided (remove leading/trailing slashes for clean joining)
    clean_prefix = ""
    clean_suffix = ""
    locked_segments = set()

    if prefix:
        clean_prefix = prefix.strip("/") + "/"
        locked_segments |= set(seg for seg in prefix.strip("/").split("/") if seg)
    if suffix:
        clean_suffix = "/" + suffix.strip("/")
        locked_segments |= set(seg for seg in suffix.strip("/").split("/") if seg)

    repeats_active = allow_repeats or bool(repeat_set)

    if locked_segments:
        # Words that are allowed to repeat should stay in the pool even if
        # they're also used in the prefix/suffix, so they can still show up
        # again in the permuted body. Only non-repeatable locked words get
        # removed from the pool entirely.
        if allow_repeats:
            protected = locked_segments  # everything is repeat-eligible
        elif repeat_set:
            protected = locked_segments & repeat_set
        else:
            protected = set()

        to_exclude = locked_segments - protected
        excluded = [w for w in words if w in to_exclude]
        if excluded:
            words = [w for w in words if w not in to_exclude]
            print(f"[+] Excluding {len(excluded)} non-repeatable word(s) already in prefix/suffix "
                  f"(case-sensitive): {excluded}", file=sys.stderr)
            print(f"[+] {len(words)} word(s) remain for permutation after exclusion.", file=sys.stderr)

        kept = sorted(w for w in words if w in locked_segments)
        if kept:
            print(f"[+] Keeping {kept} in the pool despite being used in the prefix/suffix, "
                  f"since they're allowed to repeat.", file=sys.stderr)

    if clean_prefix:
        print(f"[+] Using locked prefix: '{clean_prefix}'", file=sys.stderr)
    if clean_suffix:
        print(f"[+] Using locked suffix: '{clean_suffix}'", file=sys.stderr)
    if extensions:
        print(f"[+] Appending extensions: {extensions}", file=sys.stderr)

    # Repeat mode + cap
    repeatable_set = set(words) if allow_repeats else (repeat_set if repeat_set else set())
    if allow_repeats:
        print(f"[+] Repeats allowed: words may appear more than once per path.", file=sys.stderr)
    if repeats_active:
        print(f"[+] Max repeats per eligible word: {max_word_repeat}", file=sys.stderr)

    # Exclude list
    exclude_set = load_exclude_set(exclude_file)
    if exclude_set:
        print(f"[+] Loaded {len(exclude_set)} line(s) to exclude from '{exclude_file}'.", file=sys.stderr)

    print(f"[+] Generating structural directory permutations up to depth {max_depth}...", file=sys.stderr)

    if not repeats_active and max_depth > len(words):
        print(f"[!] Depth {max_depth} exceeds the number of available words ({len(words)}). "
              f"Depths above {len(words)} will produce 0 variations, since permutations "
              f"can't be longer than the pool of words being permuted.", file=sys.stderr)

    ext_count = len(extensions) if extensions else 0

    # ---------------------- SAMPLE MODE ----------------------
    if sample_n is not None:
        if dry_run:
            estimated_total = estimate_total(len(words), max_depth, repeats_active, ext_count)
            print(f"[i] Dry run: would attempt to randomly sample {sample_n} path(s) "
                  f"from a space of up to ~{estimated_total:,} lines (upper bound).", file=sys.stderr)
            return

        rng = random.Random()
        seen = set()
        out_file = open(output_file, 'w', encoding='utf-8') if output_file else None
        lines_written = 0
        attempts = 0
        max_attempts = max(sample_n * 50, 10_000)

        try:
            while len(seen) < sample_n and attempts < max_attempts:
                attempts += 1
                depth = rng.randint(1, max_depth)

                if repeats_active:
                    combo = tuple(rng.choice(words) for _ in range(depth))
                    if not is_valid_combo(combo, repeatable_set, max_word_repeat):
                        continue
                else:
                    if depth > len(words):
                        continue
                    combo = tuple(rng.sample(words, depth))

                if combo in seen:
                    continue

                candidate_lines = build_lines(combo, clean_prefix, clean_suffix, extensions)
                if exclude_set and any(line in exclude_set for line in candidate_lines):
                    continue

                seen.add(combo)
                for line in candidate_lines:
                    if out_file:
                        out_file.write(line + "\n")
                    else:
                        print(line)
                    lines_written += 1

            if len(seen) < sample_n:
                print(f"[!] Only found {len(seen)} unique valid sample(s) after {attempts} attempts "
                      f"(requested {sample_n}). The constrained space may be smaller than requested.",
                      file=sys.stderr)

            if out_file:
                print(f"[+] Success! Wrote {lines_written} sampled path(s) to '{output_file}'.", file=sys.stderr)
            else:
                print(f"[+] Success! Printed {lines_written} sampled path(s) to screen.", file=sys.stderr)
        finally:
            if out_file:
                out_file.close()
        return

    # ---------------------- DRY-RUN (full stats, no sampling) ----------------------
    if dry_run:
        need_exact_lines = bool(exclude_set)  # only build strings if we must check exclusions
        total_count = 0
        for depth in range(1, max_depth + 1):
            depth_count = 0
            depth_iter = (itertools.product(words, repeat=depth) if repeats_active
                          else itertools.permutations(words, depth))
            for combo in depth_iter:
                if repeats_active and not is_valid_combo(combo, repeatable_set, max_word_repeat):
                    continue
                if need_exact_lines:
                    lines = build_lines(combo, clean_prefix, clean_suffix, extensions)
                    lines = [l for l in lines if l not in exclude_set]
                    depth_count += len(lines)
                else:
                    depth_count += 1 + ext_count
            print(f"  -> [dry-run] Would generate {depth_count} variations at depth {depth}", file=sys.stderr)
            total_count += depth_count
        print(f"[+] Dry run complete. Would generate {total_count} permutated path(s). Nothing was written.", file=sys.stderr)
        return

    # ---------------------- PRE-FLIGHT SIZE WARNING ----------------------
    estimated_total = estimate_total(len(words), max_depth, repeats_active, ext_count)
    if estimated_total > confirm_threshold and not assume_yes:
        bound_note = " (upper bound; repeats/caps/exclusions may produce fewer)" if repeats_active or exclude_set else ""
        print(f"[!] This will generate approximately {estimated_total:,} lines{bound_note}.", file=sys.stderr)
        try:
            answer = input("[?] Continue? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
            print()
        if answer != "y":
            print("[-] Aborted by user.", file=sys.stderr)
            sys.exit(1)

    # ---------------------- FULL GENERATION ----------------------
    total_count = 0
    excluded_count = 0
    out_file = None

    try:
        if output_file:
            out_file = open(output_file, 'w', encoding='utf-8')

        for depth in range(1, max_depth + 1):
            depth_count = 0
            depth_iter = (itertools.product(words, repeat=depth) if repeats_active
                          else itertools.permutations(words, depth))
            for combo in depth_iter:
                if repeats_active and not is_valid_combo(combo, repeatable_set, max_word_repeat):
                    continue

                for path_line in build_lines(combo, clean_prefix, clean_suffix, extensions):
                    if exclude_set and path_line in exclude_set:
                        excluded_count += 1
                        continue
                    if out_file:
                        out_file.write(path_line + "\n")
                    else:
                        print(path_line)
                    depth_count += 1

            print(f"  -> Generated {depth_count} variations at depth {depth}", file=sys.stderr)
            total_count += depth_count

        if exclude_set:
            print(f"[+] Skipped {excluded_count} line(s) matched in the exclude list.", file=sys.stderr)

        if out_file:
            print(f"[+] Success! Wrote {total_count} permutated paths to '{output_file}'.", file=sys.stderr)
        else:
            print(f"[+] Success! Printed {total_count} permutated paths to screen.", file=sys.stderr)

    finally:
        if out_file:
            out_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate sequential URL/API directory permutations with optional prefixes, suffixes, and extensions."
    )

    # CLI Arguments
    parser.add_argument("-i", "--input", required=True, nargs="+",
                         help="Path(s) to input single-word text file(s). Accepts multiple files, merged and deduped.")
    parser.add_argument("-o", "--output", required=False, help="Path to save the generated permuted wordlist (Prints to screen if omitted)")
    parser.add_argument("-d", "--depth", type=int, default=3, help="Maximum directory/folder depth (default: 3)")

    # Features
    parser.add_argument("-p", "--prefix", required=False, help="An optional locked prefix path (e.g., 'api/v1') forced at the beginning of every path")
    parser.add_argument("-s", "--suffix", required=False, help="An optional locked suffix path (e.g., 'health' or 'export') forced at the end of every path")
    parser.add_argument("-e", "--extension", nargs="+", required=False, help="Optional extension(s) to append to paths (e.g., -e json xml bak)")
    parser.add_argument("--allow-repeats", action="store_true",
                         help="Allow ANY word to appear more than once within a single path (uses combinations-with-repeats instead of permutations)")
    parser.add_argument("--repeat-words", required=False,
                         help="Comma-separated, case-sensitive list of specific words that are allowed to repeat within a path (e.g., --repeat-words api,v1). All other words remain non-repeating.")
    parser.add_argument("--repeat-words-file", required=False,
                         help="Path to a wordlist file (one word per line, case-sensitive) whose words are allowed to repeat within a path. Can be combined with --repeat-words.")
    parser.add_argument("--max-word-repeat", type=int, default=2,
                         help="Maximum number of times an eligible (repeat-allowed) word may appear within a single path (default: 2). Only applies when --allow-repeats or --repeat-words/--repeat-words-file is set.")
    parser.add_argument("--merge-case", action="store_true",
                         help="Treat words that only differ by case (e.g. 'Users' vs 'users') as duplicates and merge them")
    parser.add_argument("--exclude-file", required=False,
                         help="Path to a file of exact, case-sensitive output lines to skip during generation.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Report exact/estimated counts per depth and in total without writing or printing any generated paths.")
    parser.add_argument("--sample", type=int, dest="sample", default=None, metavar="N",
                         help="Instead of generating the full combinatorial space, randomly sample N unique valid paths.")
    parser.add_argument("-y", "--yes", action="store_true",
                         help="Skip the confirmation prompt for very large output runs")

    args = parser.parse_args()

    generate_api_paths(
        args.input, args.output, args.depth, args.prefix, args.suffix,
        args.extension, args.allow_repeats, args.merge_case, args.yes,
        repeat_words_csv=args.repeat_words, repeat_words_file=args.repeat_words_file,
        max_word_repeat=args.max_word_repeat, exclude_file=args.exclude_file,
        dry_run=args.dry_run, sample_n=args.sample
    )
