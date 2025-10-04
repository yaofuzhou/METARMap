#!/usr/bin/env python3

import urllib.request
import xml.etree.ElementTree as ET
import board
import neopixel
import time
from time import sleep
from datetime import datetime, timedelta, time as dtime
import math
import csv
import json
import random
import sys
import argparse

try:
    import astral
except ImportError:
    astral = None

# -------------------------
# Verbosity toggle
# -------------------------
VERBOSE = False  # When False, suppresses per-LED and per-station prints

# metar.py script iteration 1.6.0 (adds boot splash + VERBOSE flag + new API endpoint)

# ---------------------------------------------------------------------------
# ------------START OF CONFIGURATION-----------------------------------------
# ---------------------------------------------------------------------------

# NeoPixel LED Configuration
LED_COUNT        = 150            # Number of LED pixels.
LED_PIN          = board.D18      # GPIO pin connected to the pixels (18 is PCM).
LED_BRIGHTNESS   = 1.0            # Float from 0.0 (min) to 1.0 (max)
LED_ORDER        = neopixel.GRB   # Strip type and colour ordering

COLOR_VFR        = (255,0,0)      # Green (note: using GRB format on LED)
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

COLOR_WHITE = (255,255,255)

COLORS = [(0, 0, 255), (0, 127, 255), (0, 255, 0), (0, 255, 127), (0, 255, 255),
    (127, 0, 255), (127, 127, 255), (127, 255, 0), (127, 255, 127), (127, 255, 255),
    (255, 0, 0), (255, 0, 127), (255, 0, 255), (255, 127, 0), (255, 127, 127),
    (255, 127, 255), (255, 255, 0), (255, 255, 127)]

# ----- Blink/Fade functionality for Wind and Lightning -----
ACTIVATE_WINDCONDITION_ANIMATION = True
ACTIVATE_LIGHTNING_ANIMATION     = True
FADE_INSTEAD_OF_BLINK            = True
WIND_BLINK_THRESHOLD             = 15
HIGH_WINDS_THRESHOLD             = 25
ALWAYS_BLINK_FOR_GUSTS           = True
BLINK_PAUSE                      = 0.05
ISS_ANIMATION_SPEED              = 0.05
BLINK_SPEED = ISS_ANIMATION_SPEED * 16 + BLINK_PAUSE
BLINK_TOTALTIME_SECONDS          = 300

# ----- Daytime dimming of LEDs based on time of day or Sunset/Sunrise -----
ACTIVATE_DAYTIME_DIMMING         = False
USE_DYNAMIC_SUNTIME              = True
BRIGHT_TIME_START                = dtime(7,0)
DIM_TIME_START                   = dtime(19,0)
USE_SUNRISE_SUNSET               = False
LOCATION                         = "Baltimore"
TIMEZONE                         = 5  # hours to look back in METAR query

LED_BRIGHTNESS_DIM               = 0.2
LED_BRIGHTNESS_DARK              = 0.04
CONTINUOUS_BRIGHTNESS            = True

# ----- Boot splash (center-of-mass ripple) -----
# SPLASH_ENABLED     = True
# Parse a simple flag for splash control
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--splash", action="store_true", help="Play splash screen once on program start")
_args, _ = _parser.parse_known_args()
SPLASH_ENABLED = bool(_args.splash)
SPLASH_COLOR       = COLOR_WHITE   # boot splash color
SPLASH_DECAY       = 0.85          # dim per ring
SPLASH_FRAME_DELAY = 0.04          # seconds between frames
SPLASH_PAUSE_AFTER = 0.10          # small clear pause after splash

# ----- Show a set of Legend LEDS at the end -----
SHOW_LEGEND = False
OFFSET_LEGEND_BY = 0
# Legend order:
# VFR, MVFR, IFR, LIFR, LIGHTNING, WINDY, HIGH WINDS

# ----- ISS Animation optimization -----
ISS_MAX_RING_RADIUS = 11  # Largest ring radius from the animation

# ---------------------------------------------------------------------------
# ------------END OF CONFIGURATION-------------------------------------------
# ---------------------------------------------------------------------------

print("Running metar.py at " + datetime.now().strftime('%d/%m/%Y %H:%M'))
print("Wind animation:" + str(ACTIVATE_WINDCONDITION_ANIMATION))
print("Lightning animation:" + str(ACTIVATE_LIGHTNING_ANIMATION))
print("Daytime Dimming:" + str(ACTIVATE_DAYTIME_DIMMING) + (" using Sunrise/Sunset" if USE_SUNRISE_SUNSET and ACTIVATE_DAYTIME_DIMMING else ""))

# Figure out sunrise/sunset times if astral is being used
if astral is not None and USE_SUNRISE_SUNSET:
    try:
        # For older clients running python 3.5 (Astral 1.10.1)
        ast = astral.Astral()
        try:
            city = ast[LOCATION]
        except KeyError:
            print("Error: Location not recognized, please check list of supported cities and reconfigure")
        else:
            if VERBOSE:
                print(city)
            sun = city.sun(date = datetime.now().date(), local = True)
            BRIGHT_TIME_START = sun['sunrise'].time()
            DIM_TIME_START = sun['sunset'].time()
    except AttributeError:
        # newer Raspberry Pi (Python 3.6+) using Astral 2.2
        import astral.geocoder
        import astral.sun
        try:
            city = astral.geocoder.lookup(LOCATION, astral.geocoder.database())
        except KeyError:
            print("Error: Location not recognized, please check list of supported cities and reconfigure")
        else:
            if VERBOSE:
                print(city)
            sun = astral.sun.sun(city.observer, date = datetime.now().date(), tzinfo=city.timezone)
            BRIGHT_TIME_START = sun['sunrise'].time()
            DIM_TIME_START = sun['sunset'].time()
    print("Sunrise:" + BRIGHT_TIME_START.strftime('%H:%M') + " Sunset:" + DIM_TIME_START.strftime('%H:%M'))

# Global state for ISS overlay
last_iss_update_time = datetime.min
iss_position = None

def get_iss_location():
    url = "http://api.open-notify.org/iss-now.json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data['iss_position']
    except Exception as e:
        if VERBOSE:
            print(f"Error fetching ISS location: {e}")
        return None

def should_update_iss_position():
    global last_iss_update_time
    current_time = datetime.now()
    if (current_time - last_iss_update_time).total_seconds() >= 5:
        last_iss_update_time = current_time
        return True
    return False

# Geometry helper
def calculate_euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def _draw_ring_frame(center_x, center_y, inner_rad, outer_rad, color, airports_data, pixels, current_led_colors):
    """Draw one ring frame just like ISS logic: set LEDs within [inner_rad, outer_rad)."""
    for i, airport in enumerate(airports_data[:LED_COUNT]):
        ax, ay = airport['lon'], airport['lat']
        d = calculate_euclidean_distance(center_x, center_y, ax, ay)
        pixels[i] = color if (inner_rad <= d < outer_rad) else current_led_colors[i]

# ISS ripple (blocking, as before)
def light_up_iss_rings(iss_x, iss_y, airports_data, pixels, current_led_colors, ring_color, dimming_factor):
    radii = [(0, 1), (0.5, 1.5), (1, 2), (1.5, 2.5), (2, 3), (2.5, 3.5), (3, 4), (3.5, 4.5), (4, 5), (4.5, 5.5), (5, 6), (5.5, 6.5), (6, 7), (6.5, 7.5), (7, 8), (7.5, 8.5)]
    for index, (inner_rad, outer_rad) in enumerate(radii):
        scaled_color = tuple(int(component * dimming_factor ** index) for component in ring_color)
        for i, airport in enumerate(airports_data):
            if i >= LED_COUNT:
                break
            airport_x, airport_y = airport['lon'], airport['lat']
            distance = calculate_euclidean_distance(iss_x, iss_y, airport_x, airport_y)
            if inner_rad <= distance < outer_rad:
                pixels[i] = scaled_color
            else:
                pixels[i] = current_led_colors[i]
        pixels.show()
        sleep(ISS_ANIMATION_SPEED)

        # After the last ring, restore the LEDs to their original state
        if index == len(radii) - 1:
            for i, color in enumerate(current_led_colors[:LED_COUNT]):
                pixels[i] = color
            pixels.show()

# -------------------------
# Boot Splash (fixed center ripple)
# -------------------------
def play_boot_splash(pixels, airports_data, color=SPLASH_COLOR,
                     decay=SPLASH_DECAY, frame_delay=SPLASH_FRAME_DELAY, pause_after=SPLASH_PAUSE_AFTER):
    """
    Boot splash: center is fixed at lat=38.375833, lon=-81.593056.
    Plays ripple outward then inward using the same ISS animation logic.
    """

    if not airports_data:
        return
    cx = -81.593056
    cy = 38.375833

    # Background snapshot (all off for splash)
    bg = [COLOR_CLEAR] * min(len(airports_data), LED_COUNT)

    # Build radii windows (same as ISS animation, outward then inward)
    radii = [(0, 1), (0.5, 1.5), (1, 2), (1.5, 2.5), (2, 3),
             (2.5, 3.5), (3, 4), (3.5, 4.5), (4, 5), (4.5, 5.5),
             (5, 6), (5.5, 6.5), (6, 7), (6.5, 7.5), (7, 8), (7.5, 8.5),
             (8, 9), (8.5, 9.5), (9, 10), (9.5, 10.5), (10, 11)]

    # OUTWARD ripple
    for idx, (inner_r, outer_r) in enumerate(radii):
        scaled_color = tuple(int(c * (decay ** idx)) for c in color)
        for i, a in enumerate(airports_data[:LED_COUNT]):
            d = calculate_euclidean_distance(cx, cy, a['lon'], a['lat'])
            pixels[i] = scaled_color if inner_r <= d < outer_r else bg[i]
        pixels.show()
        time.sleep(frame_delay)

    # INWARD ripple (reverse radii)
    for idx, (inner_r, outer_r) in enumerate(reversed(radii)):
        scaled_color = tuple(int(c * (decay ** idx)) for c in color)
        for i, a in enumerate(airports_data[:LED_COUNT]):
            d = calculate_euclidean_distance(cx, cy, a['lon'], a['lat'])
            pixels[i] = scaled_color if inner_r <= d < outer_r else bg[i]
        pixels.show()
        time.sleep(frame_delay)

    # Clear after splash
    for i in range(min(len(airports_data), LED_COUNT)):
        pixels[i] = COLOR_CLEAR
    pixels.show()
    time.sleep(pause_after)

# -------------------------
# Program start
# -------------------------
print("Initializing LEDs...")
bright = BRIGHT_TIME_START < datetime.now().time() < DIM_TIME_START
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, pixel_order=LED_ORDER, auto_write=False)

# Read the airports file and store latitude and longitude
airports_data = []
airports = []
with open("/home/pi/METARMap/airports.csv", newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        airports_data.append({
            'code': row['code'],
            'lat': float(row['lat']),
            'lon': float(row['lon'])
        })
        airports.append(row['code'])

# Calculate map coverage boundaries for ISS animation optimization
map_min_lat = map_min_lon = float('inf')
map_max_lat = map_max_lon = float('-inf')
for airport in airports_data:
    if airport['code'] != 'NULL':
        lat = airport['lat']
        lon = airport['lon']
        if lat != 0:
            map_min_lat = min(map_min_lat, lat)
            map_max_lat = max(map_max_lat, lat)
        if lon != 0:
            map_min_lon = min(map_min_lon, lon)
            map_max_lon = max(map_max_lon, lon)

# Extend boundaries by the maximum ring radius
map_min_lat -= ISS_MAX_RING_RADIUS
map_max_lat += ISS_MAX_RING_RADIUS
map_min_lon -= ISS_MAX_RING_RADIUS
map_max_lon += ISS_MAX_RING_RADIUS

# Initialize min and max values for latitude and longitude (for holiday sparkle bounds)
min_lon = min_lat = float('inf')
max_lon = max_lat = float('-inf')
for airport in airports_data:
    lat = airport['lat']
    lon = airport['lon']
    if lat != 0:
        min_lat = min(min_lat, lat)
        max_lat = max(max_lat, lat)
    if lon != 0:
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)
min_lon, max_lon = min_lon+(max_lon-min_lon)/5, max_lon-(max_lon-min_lon)/5
min_lat, max_lat = min_lat+(max_lat-min_lat)/5, max_lat-+(max_lat-min_lat)/5

# display subset (if any)
try:
    with open("/home/pi/METARMap/displayairports") as f2:
        displayairports = f2.readlines()
    displayairports = [x.strip() for x in displayairports]
    print("Using subset airports for LED display")
except IOError:
    print("Rotating through all airports on LED display")
    displayairports = None

# -------------------------
# Boot splash before weather is shown
# -------------------------
if SPLASH_ENABLED:
    if VERBOSE:
        print("Playing boot splash...")
    play_boot_splash(pixels, airports_data)

# ---------------------------------------------------------------------------
# Retrieve METAR from aviationweather.gov Data API (XML)- minimal change
# ---------------------------------------------------------------------------
ids = ",".join([item for item in airports if item != "NULL"])
url = f"https://aviationweather.gov/api/data/metar?ids={ids}&hours={TIMEZONE}&format=xml"
print(url)

req = urllib.request.Request(
    url,
    headers={'User-Agent': 'METARMap/1.0 (+raspberrypi)'}
)
content = urllib.request.urlopen(req, timeout=10).read()

# Parse XML and build conditionDict
root = ET.fromstring(content)
conditionDict = {}
stationList = []

for metar in root.iter('METAR'):
    stationId = metar.find('station_id').text if metar.find('station_id') is not None else None
    if not stationId:
        continue
    if metar.find('flight_category') is None:
        if VERBOSE:
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
    obsTime = datetime.now()

    if metar.find('wind_gust_kt') is not None:
        try:
            windGustSpeed = int(metar.find('wind_gust_kt').text)
            windGust = True if (ALWAYS_BLINK_FOR_GUSTS or windGustSpeed > WIND_BLINK_THRESHOLD) else False
        except:
            windGustSpeed = 0
            windGust = False
    if metar.find('wind_speed_kt') is not None:
        try:
            windSpeed = int(metar.find('wind_speed_kt').text)
        except:
            windSpeed = 0
    if metar.find('wind_dir_degrees') is not None:
        windDir = metar.find('wind_dir_degrees').text or ""
    if metar.find('temp_c') is not None:
        try:
            tempC = int(round(float(metar.find('temp_c').text)))
        except:
            tempC = 0
    if metar.find('dewpoint_c') is not None:
        try:
            dewpointC = int(round(float(metar.find('dewpoint_c').text)))
        except:
            dewpointC = 0
    if metar.find('visibility_statute_mi') is not None:
        try:
            vis = int(round(float(metar.find('visibility_statute_mi').text.replace('+', ''))))
        except:
            vis = 0
    if metar.find('altim_in_hg') is not None:
        try:
            altimHg = float(round(float(metar.find('altim_in_hg').text), 2))
        except:
            altimHg = 0.0
    if metar.find('wx_string') is not None:
        obs = metar.find('wx_string').text or ""
    if metar.find('observation_time') is not None:
        try:
            obsTime = datetime.fromisoformat(metar.find('observation_time').text.replace("Z","+00:00"))
        except:
            obsTime = datetime.now()
    for skyIter in metar.iter("sky_condition"):
        try:
            base = skyIter.get("cloud_base_ft_agl", default=0)
        except TypeError:
            base = skyIter.get("cloud_base_ft_agl")
        try:
            base = int(base or 0)
        except:
            base = 0
        skyCond = { "cover" : skyIter.get("sky_cover"), "cloudBaseFt": base }
        skyConditions.append(skyCond)

    rawText = metar.find('raw_text').text if metar.find('raw_text') is not None else ""
    lightning = False if ((rawText.find('LTG', 4) == -1 and rawText.find('TS', 4) == -1) or rawText.find('TSNO', 4) != -1) else True

    if VERBOSE:
        print(stationId + ":" 
        + str(flightCategory if flightCategory is not None else "") + ":" 
        + (str(windDir) if windDir is not None else "") + "@" + str(windSpeed) + ("G" + str(windGustSpeed) if windGust else "") + ":"
        + str(vis) + "SM:"
        + (str(obs) if obs is not None else "") + ":"
        + str(tempC) + "/"
        + str(dewpointC) + ":"
        + str(altimHg) + ":"
        + ("True" if lightning else "False"))

    conditionDict[stationId] = {
        "flightCategory": flightCategory,
        "windDir": windDir,
        "windSpeed": windSpeed,
        "windGustSpeed": windGustSpeed,
        "windGust": windGust,
        "vis": vis,
        "obs": obs,
        "tempC": tempC,
        "dewpointC": dewpointC,
        "altimHg": altimHg,
        "lightning": lightning,
        "skyConditions": skyConditions,
        "obsTime": obsTime
    }
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
    iteration_start_time = time.time()
    
    i = 0
    for airportcode in airports:
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
            t1 = datetime.combine(today, t1)
            t2 = datetime.combine(today, t2)
            t3 = datetime.combine(today, t3)
            t4 = datetime.combine(today, t4)
            if t2 < t1: t2 += timedelta(days=1)
            if t3 < t2: t3 += timedelta(days=1)
            if t4 < t3: t4 += timedelta(days=1)
        except:
            brightness_adjustment = 1

        t = current_utc_datetime

        if conditions is not None:
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

            windy = True if (ACTIVATE_WINDCONDITION_ANIMATION and windCycle and (conditions["windSpeed"] >= WIND_BLINK_THRESHOLD or conditions["windGust"])) else False
            highWinds = True if (windy and HIGH_WINDS_THRESHOLD != -1 and (conditions["windSpeed"] >= HIGH_WINDS_THRESHOLD or conditions["windGustSpeed"] >= HIGH_WINDS_THRESHOLD)) else False
            lightningConditions = True if (ACTIVATE_LIGHTNING_ANIMATION and (not windCycle) and conditions["lightning"]) else False

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

        if VERBOSE:
            print(f"Setting LED {i} for {airportcode or 'Unknown'} to "
                  f"{'lightning ' if lightningConditions else ''}"
                  f"{'very ' if highWinds else ''}"
                  f"{'windy ' if windy else ''}"
                  f"{conditions.get('flightCategory', 'None') if conditions else 'None'} "
                  f"{color if color is not None else 'No Color'}")
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
        if ACTIVATE_LIGHTNING_ANIMATION:
            pixels[i + OFFSET_LEGEND_BY + 4] = COLOR_LIGHTNING if windCycle else COLOR_VFR
        if ACTIVATE_WINDCONDITION_ANIMATION:
            pixels[i + OFFSET_LEGEND_BY + 5] = COLOR_VFR if not windCycle else (COLOR_VFR_FADE if FADE_INSTEAD_OF_BLINK else COLOR_CLEAR)
            if HIGH_WINDS_THRESHOLD != -1:
                pixels[i + OFFSET_LEGEND_BY + 6] = COLOR_VFR if not windCycle else COLOR_HIGH_WINDS

    # Update actual LEDs all at once
    pixels.show()

    current_led_colors = [pixels[i] for i in range(LED_COUNT)]

    # Check if it's time to update ISS position
    if should_update_iss_position():
        iss_position = get_iss_location()

    if iss_position:
        try:
            iss_x = float(iss_position['longitude'])
            iss_y = float(iss_position['latitude'])
            
            # Only animate ISS if it's within the extended map coverage area
            if map_min_lat <= iss_y <= map_max_lat and map_min_lon <= iss_x <= map_max_lon:
                if VERBOSE:
                    print("ISS lat lon:", iss_y, iss_x)
                light_up_iss_rings(iss_x, iss_y, airports_data, pixels, current_led_colors, COLOR_WHITE, 1.00)
        except Exception as e:
            if VERBOSE:
                print(f"Error in ISS animation: {e}")

    current_time = datetime.now()
    # Holiday sparkle windows (random ISS-like rings)
    if (current_time.month == 12 and current_time.day == 25 and current_time.hour == 0 and current_time.minute < 15) or \
       (current_time.month == 1 and current_time.day == 1 and current_time.hour == 0 and current_time.minute < 15) or \
       (current_time.month == 7 and current_time.day == 4 and current_time.hour == 0 and current_time.minute < 15) or \
       (current_time.month == 12 and current_time.day == 13 and current_time.hour == 15 and current_time.minute < 15):
        x = random.uniform(min_lon, max_lon)
        y = random.uniform(min_lat, max_lat)
        ring_color = random.choice(COLORS)
        light_up_iss_rings(x, y, airports_data, pixels, current_led_colors, ring_color, 1.0)

    # Sleep for remaining time to maintain consistent cycle timing
    elapsed = time.time() - iteration_start_time
    remaining = BLINK_SPEED - elapsed
    if remaining > 0:
        sleep(remaining)
    else:
        # If we're already over time, minimal sleep to prevent tight loop
        sleep(0.01)
    
    windCycle = not windCycle
    looplimit -= 1

print("Done")