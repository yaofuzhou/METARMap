#!/bin/bash

# Function to wait for internet connection
wait_for_internet() {
  local test_ip
  test_ip=8.8.8.8

  # Wait for internet up to 5 minutes
  local timeout=300

  while [ $timeout -gt 0 ]; do
    if ping -c 1 $test_ip &> /dev/null; then
      echo "Internet is up"
      return 0
    else
      echo "Waiting for internet connection..."
      sleep 10
      timeout=$((timeout-10))
    fi
  done

  echo "Timed out waiting for internet connection. Please check your network settings."
  return 1
}

# Call the function to wait for internet connection
wait_for_internet || exit 1

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
