#!/bin/bash

# Turn off the LEDs
./lightsoff.sh

# Update the suntimes.csv for the next use
echo "Updating suntimes.csv for the next use..."
sudo python3 suntimes.py

# Create a stop_refresh file to signal the refresh loop to stop
touch stop_refresh
