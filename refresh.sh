#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

stop_by_pidfile() {
  local f="$1"
  if [[ -f "$f" ]]; then
    local pid
    pid=$(cat "$f" || true)
    if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
      sudo kill "$pid" || true
      for _ in {1..10}; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.2
      done
    fi
    rm -f "$f"
  fi
}

# Ensure pixelsoff isn't still running from a previous call
stop_by_pidfile ./offpid.pid

echo "Starting metar.py"

# Extra safety: if a stray metar.py exists (launched outside this flow), stop it
if [[ -f ./metarpid.pid ]]; then
  stop_by_pidfile ./metarpid.pid
fi

# Launch metar.py; let it run to completion (no timeout)
sudo /usr/bin/python3 /home/pi/METARMap/metar.py &
echo $! > ./metarpid.pid

# Wait until it finishes, then clean pidfile
wait "$(cat ./metarpid.pid)" || true
rm -f ./metarpid.pid

echo "metar.py completed"
