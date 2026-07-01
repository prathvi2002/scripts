import itertools
import argparse
import sys
import os

def generate_api_paths(input_file, output_file, max_depth, prefix, extensions):
    """
    Reads a single-word wordlist, builds sequential directory permutations,
    applies optional locked prefixes and trailing extensions, and outputs them.
    """
    if not os.path.exists(input_file):
        print(f"[-] Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    # Read distinct, clean words from the wordlist
    with open(input_file, 'r', encoding='utf-8') as f:
        words = sorted(list(set(line.strip() for line in f if line.strip())))

    # Format prefix if provided (remove leading/trailing slashes for clean joining)
    clean_prefix = ""
    if prefix:
        clean_prefix = prefix.strip("/") + "/"

    # Print log messages to stderr so they don't corrupt stdout redirection
    print(f"[+] Loaded {len(words)} unique base words from '{input_file}'.", file=sys.stderr)
    if clean_prefix:
        print(f"[+] Using locked prefix: '{clean_prefix}'", file=sys.stderr)
    if extensions:
        print(f"[+] Appending extensions: {extensions}", file=sys.stderr)
    print(f"[+] Generating structural directory permutations up to depth {max_depth}...", file=sys.stderr)

    total_count = 0
    out_file = None

    try:
        if output_file:
            out_file = open(output_file, 'w', encoding='utf-8')

        # Generate permutations for depths 1 up to max_depth
        for depth in range(1, max_depth + 1):
            depth_count = 0
            for p in itertools.permutations(words, depth):
                # Join the permutated base words together
                base_path = "/".join(p)
                
                # Combine with the locked prefix if it exists
                full_path = f"{clean_prefix}{base_path}"
                
                # Create variations with extensions if specified
                paths_to_write = [full_path]
                if extensions:
                    for ext in extensions:
                        # Clean up dot notation (e.g., 'json' or '.json' -> '.json')
                        clean_ext = ext if ext.startswith(".") else f".{ext}"
                        paths_to_write.append(f"{full_path}{clean_ext}")

                # Write or print the generated strings
                for path_line in paths_to_write:
                    if out_file:
                        out_file.write(path_line + "\n")
                    else:
                        print(path_line)
                    depth_count += 1
            
            print(f"  -> Generated {depth_count} variations at depth {depth}", file=sys.stderr)
            total_count += depth_count

        if out_file:
            print(f"[+] Success! Wrote {total_count} permutated paths to '{output_file}'.", file=sys.stderr)
        else:
            print(f"[+] Success! Printed {total_count} permutated paths to screen.", file=sys.stderr)

    finally:
        if out_file:
            out_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate sequential URL/API directory permutations with optional prefixes and extensions."
    )
    
    # CLI Arguments
    parser.add_argument("-i", "--input", required=True, help="Path to the input single-word text file")
    parser.add_argument("-o", "--output", required=False, help="Path to save the generated permuted wordlist (Prints to screen if omitted)")
    parser.add_argument("-d", "--depth", type=int, default=3, help="Maximum directory/folder depth (default: 3)")
    
    # New Features
    parser.add_argument("-p", "--prefix", required=False, help="An optional locked prefix path (e.g., 'api/v1') forced at the beginning of every path")
    parser.add_argument("-e", "--extension", nargs="+", required=False, help="Optional extension(s) to append to paths (e.g., -e json xml bak)")

    args = parser.parse_args()
    
    generate_api_paths(args.input, args.output, args.depth, args.prefix, args.extension)
