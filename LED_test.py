import board
import neopixel
import csv

# NeoPixel LED Configuration
LED_COUNT = 150            # Number of LED pixels.
LED_PIN = board.D18        # GPIO pin connected to the pixels (18 is PCM).
LED_ORDER = neopixel.GRB   # Strip type and colour ordering
LED_BRIGHTNESS = 1.0       # Float from 0.0 (min) to 1.0 (max)

# Color definitions
COLOR_PURPLE = (128, 0, 128)
COLOR_BLACK = (0, 0, 0)
COLOR_GOLD = (255, 215, 0)
COLOR_DEEP_PINK = (255, 20, 147)
COLOR_RED = (255, 0, 0)
COLOR_ORANGE = (255, 165, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_GREEN = (0, 128, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_INDIGO = (75, 0, 130)
COLOR_VIOLET = (238, 130, 238)
COLORS = [COLOR_BLACK, COLOR_BLACK, COLOR_BLACK, COLOR_BLACK]

# Custom color assignments for specific airports
custom_colors = {
    'KTVC': COLOR_RED,
    'KAPN': COLOR_ORANGE,
    'KMBS': COLOR_YELLOW,
    'KLAN': COLOR_GREEN,
    'KFNT': COLOR_BLUE,
    'KDTW': COLOR_INDIGO,
    'KCLE': COLOR_VIOLET
}

# Initialize the LED strip
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, pixel_order=LED_ORDER, auto_write=False)

# Read the airports file and store the codes
airport_codes = []
with open("/home/pi/METARMap/airports.csv", newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['code'] != "NULL":  # Skip "NULL" entries
            airport_codes.append(row['code'])

# Set LED colors based on the cyclic pattern of defined colors or specific custom color
for i, code in enumerate(airport_codes):
    if code in custom_colors:
        pixels[i] = custom_colors[code]  # Use custom color if specified
    else:
        color_index = i % len(COLORS)  # Cycle through the color list
        pixels[i] = COLORS[color_index]  # Default cyclic pattern color

# Update the LEDs to display the colors
pixels.show()

print("LEDs updated with airport codes and custom colors.")
