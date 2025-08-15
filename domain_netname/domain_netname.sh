#!/bin/bash

# Default concurrency
MAX_CONCURRENT=5
COLOUR_OUTPUT=1

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --concurrency|-c)
            MAX_CONCURRENT="$2"
            shift 2
            ;;
        --nocolour)
            COLOUR_OUTPUT=0
            shift
            ;;
        *)
            echo "Usage: $0 [--concurrency N | -c N] [--nocolour]"
            exit 1
            ;;
    esac
done

# Validate concurrency
if ! [[ "$MAX_CONCURRENT" =~ ^[0-9]+$ ]] || [ "$MAX_CONCURRENT" -lt 1 ]; then
    echo "[!] Invalid concurrency value: $MAX_CONCURRENT"
    exit 1
fi

# Color codes
if [ $COLOUR_OUTPUT -eq 1 ]; then
    GREEN="\033[92m"
    RED="\033[91m"
    BLUE="\033[94m"
    RESET="\033[0m"
else
    GREEN=""
    RED=""
    BLUE=""
    RESET=""
fi

# Semaphore setup
SEMAPHORE="/tmp/domain_netname_semaphore.$$"
trap "rm -f $SEMAPHORE" EXIT

mkfifo "$SEMAPHORE"
exec 9<>"$SEMAPHORE"
rm "$SEMAPHORE"
i=0
while [ $i -lt "$MAX_CONCURRENT" ]; do
    echo >&9
    i=$((i+1))
done

# Check required commands
command -v aaaaa >/dev/null 2>&1 || { echo "aaaaa is required but not installed"; exit 1; }
command -v whois >/dev/null 2>&1 || { echo "whois is required but not installed"; exit 1; }

# Function to process one domain
process_domain() {
    local domain="$1"
    [[ -z "$domain" ]] && return

    echo "$domain" | aaaaa --nocolour | while read -r ip resolved_domain; do
        [[ -z "$ip" ]] && continue
        if netname=$(whois "$ip" 2>/dev/null | awk -F: '/NetName/ {gsub(/^[ \t]+/, "", $2); print $2; exit}'); then
            if [[ -n "$netname" ]]; then
                echo -e "${netname} ${ip} ${resolved_domain}"
            else
                echo -e "${RED}[!] No NetName found for $ip ($resolved_domain)${RESET}"
            fi
        else
            echo -e "${RED}[!] whois failed for $ip ($resolved_domain)${RESET}"
        fi
    done
}

# Read domains from stdin
while read -r domain; do
    # Acquire a slot in the semaphore
    read -u 9
    {
        process_domain "$domain"
        # Release the slot
        echo >&9
    } &
done

wait

