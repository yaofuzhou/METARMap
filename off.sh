#!/bin/bash

# Turn off the LEDs
./lightsoff.sh

# Update the suntimes.csv for the next use
if [ ! -f "$SUNTIMES_CSV" ] || [ "$(date -r "$SUNTIMES_CSV" +%Y-%m-%d)" != "$(date +%Y-%m-%d)" ]; then
  echo "Updating suntimes.csv..."
  sudo python3 suntimes.py
fi
echo "Good to go tomorrow!"
