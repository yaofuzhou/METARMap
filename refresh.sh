/usr/bin/sudo pkill -F /home/pi/METARMap-master/offpid.pid
/usr/bin/sudo pkill -F /home/pi/METARMap-master/metarpid.pid
/usr/bin/sudo /usr/bin/python3 /home/pi/METARMap-master/metar.py & echo $! > /home/pi/METARMap-master/metarpid.pid
