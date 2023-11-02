#!/bin/bash

# Main loop
while true; do
  # Check if the stop_refresh file exists. If it does, exit the loop.
  if [ -f stop_refresh ]; then
    echo "Found stop_refresh file. Exiting."
    break
  fi

  /usr/bin/sudo pkill -F /home/pi/METARMap/offpid.pid
  /usr/bin/sudo pkill -F /home/pi/METARMap/metarpid.pid
  /usr/bin/sudo /usr/bin/python3 /home/pi/METARMap/metar.py & echo $! > /home/pi/METARMap/metarpid.pid


  # Sleep for 300 seconds (5 minutes) before running again
  sleep 300
done
