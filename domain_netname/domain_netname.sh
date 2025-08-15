#!/bin/bash

# Check for required command
command -v aaaaa >/dev/null 2>&1 || { echo "aaaaa is required but not installed"; exit 1; }
command -v whois >/dev/null 2>&1 || { echo "whois is required but not installed"; exit 1; }

# Read domains from stdin
while read -r domain; do
    [[ -z "$domain" ]] && continue

    # Pipe the domain into aaaaa
    echo "$domain" | aaaaa --nocolour | while read -r ip resolved_domain; do
        [[ -z "$ip" ]] && continue
        netname=$(whois "$ip" | awk -F: '/NetName/ {gsub(/^[ \t]+/, "", $2); print $2; exit}')
        echo "$netname $ip $resolved_domain"
    done
done

