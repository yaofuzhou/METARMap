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
    position = get_iss_location()
    print(f"ISS Location: Latitude {position['latitude']}, Longitude {position['longitude']}")
    time.sleep(10)  # Wait for 5 minutes
