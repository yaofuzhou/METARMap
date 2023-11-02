#!/bin/bash

# Main loop
while true; do
  # Check if the stop_refresh file exists. If it does, exit the loop.
  if [ -f stop_refresh ]; then
    echo "Found stop_refresh file. Exiting."
    break
  fi

  # Existing content of your refresh.sh script goes here...

  # Sleep for 300 seconds (5 minutes) before running again
  sleep 300
done
