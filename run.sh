#!/bin/sh -

while getopts ":r" opt; do
  case $opt in
    r) omit_suntimes_script=true ;;
    \?) echo "Invalid option: -$OPTARG" >&2 ;;
  esac
done

if [ -z "$omit_suntimes_script" ]; then
  /usr/bin/sudo /usr/bin/python3 /home/pi/METARMap/suntimes.py
fi

suntimes_has_run_today=false
while true
do
  /home/pi/METARMap/refresh.sh
  current_time=$(date +%H:%M)
  current_date=$(date +%Y-%m-%d)
  if [ "$current_time" -ge "00:01" ] && [ "$suntimes_has_run_today" = false ]; then
    /usr/bin/sudo /usr/bin/python3 /home/pi/METARMap/suntimes.py
    suntimes_has_run_today=true
    suntimes_last_run_date="$current_date"
  fi
  if [ "$current_date" != "$suntimes_last_run_date" ]; then
    suntimes_has_run_today=false
  fi
  sleep 300
done