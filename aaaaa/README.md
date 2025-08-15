# DNS Lookup Tool

`aaaaa.py` is a Python script that performs **DNS lookups** for domain names provided via **standard input**. It prioritizes **IPv4 (A records)** and falls back to **IPv6 (AAAA records)** if no IPv4 addresses are found. The script can process multiple domains in **parallel** using threads.

---

## Features

- Reads domain names from **stdin** (piped input or file).
- Resolves **IPv4 addresses** first; if none found, checks for **IPv6 addresses**.
- Supports multiple IPs per domain.
- Outputs results in a **colored format** (optional disabling with `--nocolour`).
- Parallel processing using **threading** for faster lookups.

---

## Requirements

- `host` utility installed and accessible in your PATH

⚠️ The script depends on the output format of `host`. It expects:  

- A record lines to contain `has address`
- AAAA record lines to contain `has IPv6 address`

Example output from `host`:


