"""
Takes a list of endpoints
Takes a list of parameter names
Takes one value to use for all parameters
Outputs every endpoint with every parameter applied
"""

import argparse

def generate_requests(endpoints, params, value):
    results = []

    for endpoint in endpoints:
        endpoint = endpoint.strip()

        for param in params:
            param = param.strip()
            if not param:
                continue

            # build request URL
            if "?" in endpoint:
                url = f"{endpoint}&{param}={value}"
            else:
                url = f"{endpoint}?{param}={value}"

            results.append(url)

    return results


def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="""Generate endpoint × parameter test cases.
Takes a list of endpoints
Takes a list of parameter names
Takes one value to use for all parameters
Outputs every endpoint with every parameter applied
"""
    )

    parser.add_argument("-e", "--endpoints", required=True,
                        help="File with endpoints (one per line)")
    parser.add_argument("-p", "--params", required=True,
                        help="File with parameter names (one per line)")
    parser.add_argument("-v", "--value", required=True,
                        help="Value to assign to each parameter")

    parser.add_argument("-o", "--output", help="Output file (optional)")

    args = parser.parse_args()

    endpoints = load_file(args.endpoints)
    params = load_file(args.params)

    results = generate_requests(endpoints, params, args.value)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"[+] Saved {len(results)} requests to {args.output}")
    else:
        for r in results:
            print(r)


if __name__ == "__main__":
    main()
