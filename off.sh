#!/bin/bash

# Turn off the LEDs
./lightsoff.sh

# Update the suntimes.csv for the next use
echo "Updating suntimes.csv for the next use..."
sudo python3 suntimes.py
echo "Good to go tomorrow!"
