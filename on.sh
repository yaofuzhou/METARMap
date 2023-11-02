#!/bin/bash

# Path to the suntimes.csv file
SUNTIMES_CSV="suntimes.csv"

# Check if suntimes.csv does not exist or was not updated today
if [ ! -f "$SUNTIMES_CSV" ] || [ "$(date -r "$SUNTIMES_CSV" +%Y-%m-%d)" != "$(date +%Y-%m-%d)" ]; then
  echo "Updating suntimes.csv..."
  sudo python3 suntimes.py
fi

# Remove the stop_refresh file if it exists to allow the refresh process to run
rm -f stop_refresh

# Run the refresh script in a loop
while [ ! -f stop_refresh ]; do
  ./refresh.sh
  sleep 300
done
