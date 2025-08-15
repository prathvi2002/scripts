#!/bin/python3

# This tool performs DNS lookups for domain names provided via standard input and prints the first resolved IP address/addresses for each domain. It prioritizes checking for the IPv4 address (A record) of each domain. If the IPv4 address is found, it prints it and moves to the next domain without checking for the IPv6 address. Only if the IPv4 address is not found, it then checks for the IPv6 address (AAAA record). If neither IPv4 nor IPv6 addresses are found, it moves to the next domain.

import subprocess
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed


def host_lookup(domain, timeout):
    """Performs a DNS lookup for the given domain using `host`.  Prioritizes A records; falls back to AAAA if A is absent.

    Args:
        domain (str): Domain for which DNS lookups has to be performed. Waits for max 5 seconds for a reply.

    Returns:
        None or list: Returns None if no dns records for the domain is found. Returns a list containing IPv4 or IPv6 DNS address/addresses for the domain, first tries IPv4 if its not found tries IPv6.
    """

    try:
        result_a = subprocess.check_output(f"host -W {timeout} -t a {domain}", shell=True, stderr=subprocess.DEVNULL).decode().splitlines()
        ipv4_list = [
            line.split()[-1]
            for line in result_a
            if "has address" in line
        ]
    except Exception as e:
        ipv4_list = []

    # ipv4_list is not empty, return it.
    if ipv4_list:
        return ipv4_list

    try:
        result_aaaa = subprocess.check_output(f"host -W {timeout} -t aaaa {domain}", shell=True, stderr=subprocess.DEVNULL).decode().splitlines()
        ipv6_list = [
            line.split()[-1]
            for line in result_aaaa
            if "has IPv6 address" in line
        ]
    except Exception as e:
        ipv6_list = []

    # ipv6_list is not empty, return it.
    if ipv6_list:
        return ipv6_list
    # to this point if both ipv4_list and ipv6_list is empty, return None
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This tool performs DNS lookups for domain names provided via standard input and prints the first resolved IP address/addresses for each domain. It prioritizes checking for the IPv4 address (A record) of each domain. If the IPv4 address is found, it prints it and moves to the next domain without checking for the IPv6 address. Only if the IPv4 address is not found, it then checks for the IPv6 address (AAAA record). If neither IPv4 nor IPv6 addresses are found, it moves to the next domain.", epilog = """
This tool uses the `host` utility. The version used during development was: `host 9.18.30-0ubuntu0.24.04.2-Ubuntu`

⚠️ Note: This tool depends on the output format of `host`.
It expects the A record line to contain `has address` and the AAAA record line to contain `has IPv6 address` for correct checking.

Please make sure your version of `host` produces output like this:

    example.com has address 96.7.128.198
    example.com has address 96.7.128.175
    example.com has address 23.215.0.138
    example.com has address 23.215.0.136
    example.com has address 23.192.228.84
    example.com has address 23.192.228.80
    example.com has IPv6 address 2600:1408:ec00:36::1736:7f31
    example.com has IPv6 address 2600:1408:ec00:36::1736:7f24
    example.com has IPv6 address 2600:1406:bc00:53::b81e:94ce
    example.com has IPv6 address 2600:1406:bc00:53::b81e:94c8
    example.com has IPv6 address 2600:1406:3a00:21::173e:2e66
    example.com has IPv6 address 2600:1406:3a00:21::173e:2e65
    example.com mail is handled by 0 .
""",  formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("--timeout", type=int, default=5, help="DNS query timeout in seconds (default 5)")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads to use for parallel processing (default: 10)")
    parser.add_argument(
        "--nocolour",
        action="store_true",
        help="Disable colour output. (default: False)"
    )

    args = parser.parse_args()

    timeout_value = args.timeout
    threads_value = args.threads
    nocolour_value = args.nocolour

    if nocolour_value:
        BLUE = ""
        YELLOW = ""
        RESET = ""
    else:
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        RESET = "\033[0m"

    if threads_value > 1000:
        print("Max threads can be used is 1000")
        sys.exit(1)

    # # Caution: loads all domains into memory. Maybe it is fine for large lists (even millions) on most modern systems.
    # domains = [line.strip() for line in sys.stdin if line.strip()]

    # for domain in domains:
    #     domain = domain.strip()
    #     if not domain:
    #         pass
    #     else:
    #         ips = host_lookup(domain, timeout=timeout_value)
            
    #         if not ips:
    #             pass
    #         else:
    #             # print(domain, ips)
    #             for ip in ips:
    #                 print(domain, ip)


    # Caution: loads all domains into memory. Maybe it is fine for large lists (even millions) on most modern systems.
    domains = [line.strip() for line in sys.stdin if line.strip()]

    try:
        with ThreadPoolExecutor(max_workers=threads_value) as executor:
            futures = {
                executor.submit(host_lookup, domain, timeout_value): domain
                for domain in domains
            }

            for future in as_completed(futures):
                domain = futures[future]
                try:
                    ips = future.result()
                    if ips:
                        for ip in ips:
                            print(f"{YELLOW}{ip}{RESET} {BLUE}{domain}{RESET}")
                except Exception as e:
                    pass  # You can log domain failure here if needed
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting...")
        sys.exit(0)
