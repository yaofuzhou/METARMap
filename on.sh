#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

# Single-instance guard
exec 9>./on.lock
if ! flock -n 9; then
  echo "on.sh already running; exiting."
  exit 0
fi

wait_for_internet() {
  local test_ip=8.8.8.8
  local timeout=300
  while (( timeout > 0 )); do
    if ping -c 1 "$test_ip" &>/dev/null; then
      echo "Internet is up"
      return 0
    fi
    echo "Waiting for internet connection..."
    sleep 10
    timeout=$((timeout-10))
  done
  echo "Timed out waiting for internet connection."
  return 1
}

update_suntimes_if_needed() {
  local csv="suntimes.csv"
  if [[ ! -f "$csv" ]] || [[ "$(date -r "$csv" +%Y-%m-%d)" != "$(date +%Y-%m-%d)" ]]; then
    echo "Updating suntimes.csv..."
    if ! pgrep -f "python3 .*suntimes.py" >/dev/null; then
      sudo python3 suntimes.py >/dev/null 2>&1 &
    fi
  fi
}

wait_for_internet || exit 1

# Stop any old loop and blank LEDs, then allow new loop
./lightsoff.sh || true
rm -f ./stop_refresh

# Clean up corrupt pidfiles only (do not kill here)
for f in ./offpid.pid ./metarpid.pid; do
  if [[ -f "$f" ]]; then
    pid=$(cat "$f" || true)
    [[ "$pid" =~ ^[0-9]+$ ]] || rm -f "$f"
  fi
done

# We will pass --splash only on the first run of metar.py
SPLASH_ARG="--splash"

# MAIN LOOP: metar.py runs to completion; start next cycle immediately
while [[ ! -f ./stop_refresh ]]; do
  update_suntimes_if_needed
  if [[ -n "${SPLASH_ARG}" ]]; then
    ./refresh.sh "${SPLASH_ARG}"
    SPLASH_ARG=""
  else
    ./refresh.sh
  fi
done
