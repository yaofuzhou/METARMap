import requests
import schedule
import time

# Function to print the latitude and longitude of an aircraft
def print_aircraft_location(mode_s_code):
    # Replace with the actual ADSBdB API endpoint
    api_url = f"https://api.adsbdb.com/v0/aircraft/{mode_s_code}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        if "aircraft" in data["response"]:
            latitude = data["response"]["aircraft"]["latitude"]
            longitude = data["response"]["aircraft"]["longitude"]
            print(f"Aircraft {mode_s_code} Location: Latitude = {latitude}, Longitude = {longitude}")
        else:
            print("Aircraft data not available.")
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

# Example Mode-S code for an aircraft
mode_s_code = "N3659R"

# Schedule to run every 5 seconds
schedule.every(5).seconds.do(print_aircraft_location, mode_s_code=mode_s_code)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
