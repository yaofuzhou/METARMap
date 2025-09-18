#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

# Turn LEDs off and stop the loop (may interrupt metar.py; see lightsoff.sh note)
./lightsoff.sh || true

# Update suntimes once for next start
csv="suntimes.csv"
if [[ ! -f "$csv" ]] || [[ "$(date -r "$csv" +%Y-%m-%d)" != "$(date +%Y-%m-%d)" ]]; then
  echo "Updating suntimes.csv..."
  sudo python3 suntimes.py || true
fi

# Clean pidfiles that might remain
rm -f ./metarpid.pid ./offpid.pid
