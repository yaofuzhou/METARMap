/usr/bin/sudo pkill -F /home/pi/METARMap/offpid.pid
# /usr/bin/sudo pkill -F /home/pi/METARMap/metarpid.pid
/usr/bin/sudo /usr/bin/python3 /home/pi/METARMap/pixelsoff.py & echo $! > /home/pi/METARMap/offpid.pid

# Create a stop_refresh file to signal the refresh loop to stop
touch stop_refresh
