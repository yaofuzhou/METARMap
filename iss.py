import urllib.request
import json
import time

def get_iss_location():
    url = "http://api.open-notify.org/iss-now.json"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        return data['iss_position']

# Example: Print ISS location every 5 minutes
while True:
    iss_position = get_iss_location()
    print(f"ISS Location: Latitude {iss_position['latitude']}, Longitude {iss_position['longitude']}")
    time.sleep(2)  # Wait for 2 seconds
