#!/usr/bin/env python3

import urllib.request
import xml.etree.ElementTree as ET
import board
import neopixel
import time
from time import sleep
from datetime import datetime, timedelta, time
import math
import csv

try:
    import astral
except ImportError:
    astral = None

# metar.py script iteration 1.5.1

# ---------------------------------------------------------------------------
# ------------START OF CONFIGURATION-----------------------------------------
# ---------------------------------------------------------------------------

# NeoPixel LED Configuration
LED_COUNT        = 150            # Number of LED pixels.
LED_PIN          = board.D18      # GPIO pin connected to the pixels (18 is PCM).
LED_BRIGHTNESS   = 1.0            # Float from 0.0 (min) to 1.0 (max)
LED_ORDER        = neopixel.GRB   # Strip type and colour ordering

COLOR_VFR        = (255,0,0)      # Green
COLOR_VFR_FADE   = (125,0,0)      # Green Fade for wind
COLOR_MVFR       = (0,0,255)      # Blue
COLOR_MVFR_FADE  = (0,0,125)      # Blue Fade for wind
COLOR_IFR        = (0,255,0)      # Red
COLOR_IFR_FADE   = (0,125,0)      # Red Fade for wind
COLOR_LIFR       = (0,125,125)    # Magenta
COLOR_LIFR_FADE  = (0,75,75)      # Magenta Fade for wind
COLOR_CLEAR      = (0,0,0)        # Clear
COLOR_LIGHTNING  = (255,255,255)  # White
COLOR_HIGH_WINDS = (255,255,0)    # Yellow

# ----- Blink/Fade functionality for Wind and Lightning -----
# Do you want the METARMap to be static to just show flight conditions, or do you also want blinking/fading based on current wind conditions
ACTIVATE_WINDCONDITION_ANIMATION = True             # Set this to False for Static or True for animated wind conditions
#Do you want the Map to Flash white for lightning in the area
ACTIVATE_LIGHTNING_ANIMATION     = True             # Set this to False for Static or True for animated Lightning
# Fade instead of blink
FADE_INSTEAD_OF_BLINK            = True             # Set to False if you want blinking
# Blinking Windspeed Threshold
WIND_BLINK_THRESHOLD             = 15               # Knots of windspeed to blink/fade
HIGH_WINDS_THRESHOLD             = 25               # Knots of windspeed to trigger Yellow LED indicating very High Winds, set to -1 if you don't want to use this
ALWAYS_BLINK_FOR_GUSTS           = True             # Always animate for Gusts (regardless of speeds)
# Blinking Speed in seconds
BLINK_SPEED                      = 1.0              # Float in seconds, e.g. 0.5 for half a second
# Total blinking time in seconds.
# For example set this to 300 to keep blinking for 5 minutes if you plan to run the script every 5 minutes to fetch the updated weather
BLINK_TOTALTIME_SECONDS          = 300

# ----- Daytime dimming of LEDs based on time of day or Sunset/Sunrise -----
ACTIVATE_DAYTIME_DIMMING         = False             # Set to True if you want to dim the map after a certain time of day
USE_DYNAMIC_SUNTIME              = True             # Set to True if the brightness of each LED is adjusted according to its local twilight, sunrise, and sunset times.
BRIGHT_TIME_START                = time(7,0)        # Time of day to run at LED_BRIGHTNESS in hours and minutes
DIM_TIME_START                   = time(19,0)       # Time of day to run at LED_BRIGHTNESS_DIM in hours and minutes
USE_SUNRISE_SUNSET               = False            # Set to True if instead of fixed times for bright/dimming, you want to use local sunrise/sunset
LOCATION                         = "Baltimore"      # Nearby city for Sunset/Sunrise timing, refer to https://astral.readthedocs.io/en/latest/#cities for list of cities supported

LED_BRIGHTNESS_DIM               = 0.2              # Float from 0.0 (min) to 1.0 (max)
LED_BRIGHTNESS_DARK              = 0.04             # Float from 0.0 (min) to 1.0 (max)
CONTINUOUS_BRIGHTNESS            = True             # If set to True, brightness in the twilight zone will vary continuously between LED_BRIGHTNESS_DIM and LED_BRIGHTNESS_DARK

# ----- Show a set of Legend LEDS at the end -----
SHOW_LEGEND = False            # Set to true if you want to have a set of LEDs at the end show the legend
# You'll need to add 7 LEDs at the end of your string of LEDs
# If you want to offset the legend LEDs from the end of the last airport from the airports file,
# then change this offset variable by the number of LEDs to skip before the LED that starts the legend
OFFSET_LEGEND_BY = 0
# The order of LEDs is:
#    VFR
#    MVFR
#    IFR
#    LIFR
#    LIGHTNING
#    WINDY
#    HIGH WINDS


# ---------------------------------------------------------------------------
# ------------END OF CONFIGURATION-------------------------------------------
# ---------------------------------------------------------------------------

print("Running metar.py at " + datetime.now().strftime('%d/%m/%Y %H:%M'))

# Figure out sunrise/sunset times if astral is being used
if astral is not None and USE_SUNRISE_SUNSET:
    try:
        # For older clients running python 3.5 which are using Astral 1.10.1
        ast = astral.Astral()
        try:
            city = ast[LOCATION]
        except KeyError:
            print("Error: Location not recognized, please check list of supported cities and reconfigure")
        else:
            print(city)
            sun = city.sun(date = datetime.now().date(), local = True)
            BRIGHT_TIME_START = sun['sunrise'].time()
            DIM_TIME_START = sun['sunset'].time()
    except AttributeError:
        # newer Raspberry Pi versions using Python 3.6+ using Astral 2.2
        import astral.geocoder
        import astral.sun
        try:
            city = astral.geocoder.lookup(LOCATION, astral.geocoder.database())
        except KeyError:
            print("Error: Location not recognized, please check list of supported cities and reconfigure")
        else:
            print(city)
            sun = astral.sun.sun(city.observer, date = datetime.now().date(), tzinfo=city.timezone)
            BRIGHT_TIME_START = sun['sunrise'].time()
            DIM_TIME_START = sun['sunset'].time()
    print("Sunrise:" + BRIGHT_TIME_START.strftime('%H:%M') + " Sunset:" + DIM_TIME_START.strftime('%H:%M'))



# Function to calculate Euclidean distance between two points (x1, y1) and (x2, y2)
def calculate_euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Function to light up LEDs based on ISS position and concentric rings
def light_up_iss_rings(iss_x, iss_y, airports_data, pixels, current_led_colors):
    # Radii of the concentric rings
    radii = [(0, 1), (0.5, 1.5), (1, 2), (1.5, 2.5), (2, 3), (2.5, 3.5), (3, 4), (3.5, 4.5), (4, 5), (4.5, 5.5)]
    for inner_rad, outer_rad in radii:
        for i, airport in enumerate(airports_data):
            airport_x, airport_y = airport['lon'], airport['lat']  # Treat lon as x and lat as y
            distance = calculate_euclidean_distance(iss_x, iss_y, airport_x, airport_y)
            if inner_rad <= distance < outer_rad:
                pixels[i] = (255, 255, 255)  # Light up the LED
            else:
                # Set to stored color from current_led_colors
                pixels[i] = current_led_colors[i]
        pixels.show()
        sleep(0.5)  # Each ring lasts 0.1 seconds



# Initialize the LED strip
bright = BRIGHT_TIME_START < datetime.now().time() < DIM_TIME_START
print("Wind animation:" + str(ACTIVATE_WINDCONDITION_ANIMATION))
print("Lightning animation:" + str(ACTIVATE_LIGHTNING_ANIMATION))
print("Daytime Dimming:" + str(ACTIVATE_DAYTIME_DIMMING) + (" using Sunrise/Sunset" if USE_SUNRISE_SUNSET and ACTIVATE_DAYTIME_DIMMING else ""))
# pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness = LED_BRIGHTNESS_DARK if (ACTIVATE_DAYTIME_DIMMING and bright == False) else LED_BRIGHTNESS, pixel_order = LED_ORDER, auto_write = False)
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, pixel_order=LED_ORDER, auto_write=False)


# Read the airports file and store latitude and longitude
airports_data = []
with open("/home/pi/METARMap/airports.csv", newline='') as f:
    reader = csv.DictReader(f)
    airports = [row['code'] for row in reader]
    for row in reader:
        airports_data.append({
            'code': row['code'],
            'lat': float(row['lat']),
            'lon': float(row['lon'])
        })
try:
    with open("/home/pi/METARMap/displayairports") as f2:
        displayairports = f2.readlines()
    displayairports = [x.strip() for x in displayairports]
    print("Using subset airports for LED display")
except IOError:
    print("Rotating through all airports on LED display")
    displayairports = None

# Retrieve METAR from aviationweather.gov data server
# Details about parameters can be found here: https://www.aviationweather.gov/dataserver/example?datatype=metar
hoursBeforeNow = 5
url = "https://aviationweather.gov/cgi-bin/data/metar.php?url_options&ids=" + ",".join([item for item in airports if item != "NULL"]) + "&format=xml&hours=" + str(hoursBeforeNow) + "&order=-obs"
print(url)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69'})
content = urllib.request.urlopen(req).read()

# Retrieve flying conditions from the service response and store in a dictionary for each airport
root = ET.fromstring(content)
conditionDict = { "NULL": {"flightCategory" : "", "windDir": "", "windSpeed" : 0, "windGustSpeed" :  0, "windGust" : False, "lightning": False, "tempC" : 0, "dewpointC" : 0, "vis" : 0, "altimHg" : 0, "obs" : "", "skyConditions" : {}, "obsTime" : datetime.now() } }
conditionDict.pop("NULL")
stationList = []
for metar in root.iter('METAR'):
    stationId = metar.find('station_id').text
    if metar.find('flight_category') is None:
        print("Missing flight condition, skipping.")
        continue
    flightCategory = metar.find('flight_category').text
    windDir = ""
    windSpeed = 0
    windGustSpeed = 0
    windGust = False
    lightning = False
    tempC = 0
    dewpointC = 0
    vis = 0
    altimHg = 0.0
    obs = ""
    skyConditions = []
    if metar.find('wind_gust_kt') is not None:
        windGustSpeed = int(metar.find('wind_gust_kt').text)
        windGust = (True if (ALWAYS_BLINK_FOR_GUSTS or windGustSpeed > WIND_BLINK_THRESHOLD) else False)
    if metar.find('wind_speed_kt') is not None:
        windSpeed = int(metar.find('wind_speed_kt').text)
    if metar.find('wind_dir_degrees') is not None:
        windDir = metar.find('wind_dir_degrees').text
    if metar.find('temp_c') is not None:
        tempC = int(round(float(metar.find('temp_c').text)))
    if metar.find('dewpoint_c') is not None:
        dewpointC = int(round(float(metar.find('dewpoint_c').text)))
    if metar.find('visibility_statute_mi') is not None:
        vis = int(round(float(metar.find('visibility_statute_mi').text.replace('+', ''))))
    if metar.find('altim_in_hg') is not None:
        altimHg = float(round(float(metar.find('altim_in_hg').text), 2))
    if metar.find('wx_string') is not None:
        obs = metar.find('wx_string').text
    if metar.find('observation_time') is not None:
        obsTime = datetime.fromisoformat(metar.find('observation_time').text.replace("Z","+00:00"))
    for skyIter in metar.iter("sky_condition"):
        skyCond = { "cover" : skyIter.get("sky_cover"), "cloudBaseFt": int(skyIter.get("cloud_base_ft_agl", default=0)) }
        skyConditions.append(skyCond)
    if metar.find('raw_text') is not None:
        rawText = metar.find('raw_text').text
        lightning = False if ((rawText.find('LTG', 4) == -1 and rawText.find('TS', 4) == -1) or rawText.find('TSNO', 4) != -1) else True
    print(stationId + ":" 
    + flightCategory + ":" 
    + str(windDir) + "@" + str(windSpeed) + ("G" + str(windGustSpeed) if windGust else "") + ":"
    + str(vis) + "SM:"
    + obs + ":"
    + str(tempC) + "/"
    + str(dewpointC) + ":"
    + str(altimHg) + ":"
    + str(lightning))
    conditionDict[stationId] = { "flightCategory" : flightCategory, "windDir": windDir, "windSpeed" : windSpeed, "windGustSpeed": windGustSpeed, "windGust": windGust, "vis": vis, "obs" : obs, "tempC" : tempC, "dewpointC" : dewpointC, "altimHg" : altimHg, "lightning": lightning, "skyConditions" : skyConditions, "obsTime": obsTime }
    if displayairports is None or stationId in displayairports:
        stationList.append(stationId)

# Read data from 'suntimes.csv' file
with open('suntimes.csv', newline='') as f:
    reader = csv.DictReader(f)
    suntimes = {row['code']: row for row in reader}

# Update dictionaries in 'conditionDict' with data from 'suntimes.csv'
for stationId, conditions in conditionDict.items():
    if stationId in suntimes:
        conditions.update({
            'twilight_start': suntimes[stationId]['twilight_start'],
            'sunrise': suntimes[stationId]['sunrise'],
            'sunset': suntimes[stationId]['sunset'],
            'twilight_end': suntimes[stationId]['twilight_end']
        })

# Setting LED colors based on weather conditions
looplimit = int(round(BLINK_TOTALTIME_SECONDS / BLINK_SPEED)) if (ACTIVATE_WINDCONDITION_ANIMATION or ACTIVATE_LIGHTNING_ANIMATION) else 1

windCycle = False
displayTime = 0.0
displayAirportCounter = 0
numAirports = len(stationList)
while looplimit > 0:
    i = 0
    for airportcode in airports:
        # Skip NULL entries
        if airportcode == "NULL":
            i += 1
            continue

        color = COLOR_CLEAR
        conditions = conditionDict.get(airportcode, None)
        windy = False
        highWinds = False
        lightningConditions = False

        brightness_adjustment = 1.0
        current_utc_datetime = datetime.utcnow()
        today = datetime.now().date()

        try:
            t1 = datetime.strptime(conditions['twilight_start'], '%H:%M:%S').time()
            t2 = datetime.strptime(conditions['sunrise'], '%H:%M:%S').time()
            t3 = datetime.strptime(conditions['sunset'], '%H:%M:%S').time()
            t4 = datetime.strptime(conditions['twilight_end'], '%H:%M:%S').time()
            # Convert t1, t2, t3, and t4 to datetime objects with today's date
            t1 = datetime.combine(today, t1)
            t2 = datetime.combine(today, t2)
            t3 = datetime.combine(today, t3)
            t4 = datetime.combine(today, t4)
            if t2 < t1:
                t2 += timedelta(days=1)
            if t3 < t2:
                t3 += timedelta(days=1)
            if t4 < t3:
                t4 += timedelta(days=1)
        except:
            brightness_adjustment = 1

        t = current_utc_datetime

        if conditions != None:
            # Check the position of t relative to t1, t2, t3, and t4
            if t < t1:
                brightness_adjustment = LED_BRIGHTNESS_DARK
            elif t1 <= t < t2:
                if CONTINUOUS_BRIGHTNESS:
                    t21 = (t2-t1).total_seconds()
                    dt = (t-t1).total_seconds()
                    d_brightness = LED_BRIGHTNESS_DIM - LED_BRIGHTNESS_DARK
                    brightness_adjustment = LED_BRIGHTNESS_DARK + d_brightness * dt / t21
                else:
                    brightness_adjustment = LED_BRIGHTNESS_DIM
            elif t2 <= t < t3:
                brightness_adjustment = 1.0
            elif t3 <= t < t4:
                if CONTINUOUS_BRIGHTNESS:
                    t43 = (t4-t3).total_seconds()
                    dt = (t-t3).total_seconds()
                    d_brightness = LED_BRIGHTNESS_DIM - LED_BRIGHTNESS_DARK
                    brightness_adjustment = LED_BRIGHTNESS_DIM - d_brightness * dt / t43
                else:
                    brightness_adjustment = LED_BRIGHTNESS_DIM
            else:
                brightness_adjustment = LED_BRIGHTNESS_DARK
            windy = True if (ACTIVATE_WINDCONDITION_ANIMATION and windCycle == True and (conditions["windSpeed"] >= WIND_BLINK_THRESHOLD or conditions["windGust"] == True)) else False
            highWinds = True if (windy and HIGH_WINDS_THRESHOLD != -1 and (conditions["windSpeed"] >= HIGH_WINDS_THRESHOLD or conditions["windGustSpeed"] >= HIGH_WINDS_THRESHOLD)) else False
            lightningConditions = True if (ACTIVATE_LIGHTNING_ANIMATION and windCycle == False and conditions["lightning"] == True) else False
            if conditions["flightCategory"] == "VFR":
                color = COLOR_VFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else (COLOR_VFR_FADE if FADE_INSTEAD_OF_BLINK else COLOR_CLEAR) if windy else COLOR_CLEAR
            elif conditions["flightCategory"] == "MVFR":
                color = COLOR_MVFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else (COLOR_MVFR_FADE if FADE_INSTEAD_OF_BLINK else COLOR_CLEAR) if windy else COLOR_CLEAR
            elif conditions["flightCategory"] == "IFR":
                color = COLOR_IFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else (COLOR_IFR_FADE if FADE_INSTEAD_OF_BLINK else COLOR_CLEAR) if windy else COLOR_CLEAR
            elif conditions["flightCategory"] == "LIFR":
                color = COLOR_LIFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else (COLOR_LIFR_FADE if FADE_INSTEAD_OF_BLINK else COLOR_CLEAR) if windy else COLOR_CLEAR
            else:
                color = COLOR_CLEAR

        print("Setting LED " + str(i) + " for " + airportcode + " to " + ("lightning " if lightningConditions else "") + ("very " if highWinds else "") + ("windy " if windy else "") + (conditions["flightCategory"] if conditions != None else "None") + " " + str(color))

        print("brightness_adjustment =", brightness_adjustment)

        if USE_DYNAMIC_SUNTIME:
            g, r, b = color
            g = int(float(g) * brightness_adjustment)
            r = int(float(r) * brightness_adjustment)
            b = int(float(b) * brightness_adjustment)
            pixels[i] = (g, r, b)
        else:
            pixels[i] = color
        i += 1

    # Legend
    if SHOW_LEGEND:
        pixels[i + OFFSET_LEGEND_BY] = COLOR_VFR
        pixels[i + OFFSET_LEGEND_BY + 1] = COLOR_MVFR
        pixels[i + OFFSET_LEGEND_BY + 2] = COLOR_IFR
        pixels[i + OFFSET_LEGEND_BY + 3] = COLOR_LIFR
        if ACTIVATE_LIGHTNING_ANIMATION == True:
            pixels[i + OFFSET_LEGEND_BY + 4] = COLOR_LIGHTNING if windCycle else COLOR_VFR # lightning
        if ACTIVATE_WINDCONDITION_ANIMATION == True:
            pixels[i+ OFFSET_LEGEND_BY + 5] = COLOR_VFR if not windCycle else (COLOR_VFR_FADE if FADE_INSTEAD_OF_BLINK else COLOR_CLEAR)    # windy
            if HIGH_WINDS_THRESHOLD != -1:
                pixels[i + OFFSET_LEGEND_BY + 6] = COLOR_VFR if not windCycle else COLOR_HIGH_WINDS  # high winds

    # Update actual LEDs all at once
    pixels.show()

    current_led_colors = [pixels[i] for i in range(LED_COUNT)]

    # Call the modified ISS animation function
    light_up_iss_rings(-80.3944, 36.66505, airports_data, pixels, current_led_colors)

    # Switching between animation cycles
    sleep(BLINK_SPEED)
    windCycle = False if windCycle else True
    looplimit -= 1


print("Done")
