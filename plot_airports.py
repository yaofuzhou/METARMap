# Full script including reading the CSV and plotting with optimized grid size

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def find_smallest_difference(coordinates):
    """
    Find the smallest non-zero difference between sorted coordinate values.
    """
    sorted_coords = np.sort(np.unique(coordinates))
    differences = np.diff(sorted_coords)
    # Filter out zero differences and find the minimum
    min_difference = np.min(differences[differences > 0])
    return min_difference

# Load the CSV file
file_path = './airports.csv'
airports_data = pd.read_csv(file_path)

# Filtering out coordinates (0,0)
airports_data_filtered = airports_data[(airports_data['lat'] != 0) | (airports_data['lon'] != 0)]

# Extracting latitude and longitude values
latitudes_filtered = airports_data_filtered['lat']
longitudes_filtered = airports_data_filtered['lon']

# Find the smallest non-zero differences in latitude and longitude
min_lat_diff = find_smallest_difference(latitudes_filtered)
min_lon_diff = find_smallest_difference(longitudes_filtered)
print(min_lat_diff, min_lon_diff)

# Use the smaller of the two as the grid size
grid_size = min(min_lat_diff, min_lon_diff)

# Extracting min and max values for setting plot limits
lat_min, lat_max = np.min(latitudes_filtered), np.max(latitudes_filtered)
lon_min, lon_max = np.min(longitudes_filtered), np.max(longitudes_filtered)

# Plotting the scatter plot with the determined grid size
plt.figure(figsize=(10, 10))
plt.scatter(longitudes_filtered, latitudes_filtered, marker='o', color='blue')
plt.title("Scatter Plot of Airport Coordinates with Optimized Grid Size")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)

# Setting custom grid size
plt.xticks(np.arange(np.floor(lon_min), np.ceil(lon_max) + grid_size, grid_size))
plt.yticks(np.arange(np.floor(lat_min), np.ceil(lat_max) + grid_size, grid_size))
plt.gca().set_aspect('equal', adjustable='box')

plt.show()
