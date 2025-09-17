import urllib.request
import xml.etree.ElementTree as ET

# Configuration for specific airport
airport_code = "CYYZ"
# airport_code = "KJFK"

# URL to fetch METAR data
url = f"https://aviationweather.gov/cgi-bin/data/metar.php?url_options&ids=,{airport_code}&format=xml&hours=5&order=-obs"

# Fetch METAR data
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    content = urllib.request.urlopen(req).read()
    root = ET.fromstring(content)

    # Check if METAR data element is present
    metar = root.find('data/METAR')
    if metar is None:
        print(f"METAR data for {airport_code} is not available.")
    else:
        # Extract data and handle cases where elements may be missing
        flight_category = metar.find('flight_category')
        wind_speed_elem = metar.find('wind_speed_kt')
        wx_string_elem = metar.find('wx_string')

        flight_category_text = flight_category.text if flight_category is not None else "No Data"
        wind_speed = int(wind_speed_elem.text) if wind_speed_elem is not None else 0
        lightning = "lightning " if 'LTG' in (wx_string_elem.text if wx_string_elem is not None else "") else ""

        # Determine LED color based on flight category
        colors = {
            "VFR": (0, 255, 0),
            "IFR": (255, 0, 0),
            "MVFR": (0, 0, 255),
            "LIFR": (255, 0, 255)
        }
        color = colors.get(flight_category_text, (0, 0, 0))  # Default to black if no matching category

        # Print LED settings
        print(f"Setting LED for {airport_code} to {lightning}{flight_category_text} {color}")

except Exception as e:
    print(f"Error fetching or parsing METAR data: {e}")
