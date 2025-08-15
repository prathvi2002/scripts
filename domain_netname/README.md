# Domain Whois NetName Resolver

`domain_netname.sh` is a Bash script that takes a list of domain names (via piped input) and outputs the **NetName**, **IP address**, and the **domain** for each entry (if a single domain has multiple DNS resolveable IPs, it does it for each IP). It uses [`aaaaa`](https://github.com/prathvi2002/scripts/tree/main/aaaaa) to resolve domains to IPs and `whois` to fetch network registration information.

## Features

- Accepts **piped input** (from a file or another command)
- Resolves multiple IPs per domain
- Extracts **NetName** from WHOIS records
- Outputs results in a clean, space-separated format:  

## Usage

```bash
cat domains.txt | ./domain_netname.sh
```


## Clever Usage
- You can filter the script output to show only entries for a specific target NetName using `grep`. Example:
```bash
cat domains.txt | ./domain_netname.sh | grep -i cloudflare
```


## Requirements

- [`aaaaa`](https://github.com/prathvi2002/scripts/tree/main/aaaaa) for domain resolution
- `whois` command-line tool

Make sure both `aaaaa` and `whois` are installed and available in your PATH.
