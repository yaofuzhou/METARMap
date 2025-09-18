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

# Request the loop stop (on.sh will exit after current cycle)
: > ./stop_refresh

# If you want immediate lights-off without waiting for metar.py to finish,
# we stop any running metar.py here. This does interrupt metar.py by design
# for the "off" action. If you prefer not to interrupt, comment the line below.
stop_by_pidfile ./metarpid.pid

# Stop any existing pixelsoff and start a fresh one to blank LEDs now
stop_by_pidfile ./offpid.pid
sudo /usr/bin/python3 /home/pi/METARMap/pixelsoff.py >/dev/null 2>&1 &
echo $! > ./offpid.pid
