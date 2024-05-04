import board
import neopixel
import csv

# NeoPixel LED Configuration
LED_COUNT = 150            # Number of LED pixels.
LED_PIN = board.D18        # GPIO pin connected to the pixels (18 is PCM).
LED_ORDER = neopixel.GRB   # Strip type and colour ordering
LED_BRIGHTNESS = 1.0       # Float from 0.0 (min) to 1.0 (max)

# Color definitions
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_PURPLE = (128, 0, 128)
COLORS = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_PURPLE]

# Initialize the LED strip
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, pixel_order=LED_ORDER, auto_write=False)

# Read the airports file and store the codes
airport_codes = []
with open("/home/pi/METARMap/airports.csv", newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['code'] != "NULL":  # Skip "NULL" entries
            airport_codes.append(row['code'])

# Set LED colors based on the cyclic pattern of defined colors
for i, code in enumerate(airport_codes):
    color_index = i % len(COLORS)  # Cycle through the color list
    pixels[i] = COLORS[color_index]  # Assign color to each LED based on airport code index

# Update the LEDs to display the colors
pixels.show()

print("LEDs updated with airport codes.")
