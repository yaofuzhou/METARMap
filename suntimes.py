import csv
import requests
from datetime import datetime

def get_sun_times(lat, lon):
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={today}"
    response = requests.get(url)
    data = response.json()
    return data['results']

def format_time(time_str):
    return datetime.strptime(time_str, '%I:%M:%S %p').strftime('%H:%M:%S')

# Read airport locations from CSV file and write sun times to output file
with open('airports.csv', 'r') as input_file, open('suntimes.csv', 'w') as output_file:
    reader = csv.DictReader(input_file)
    writer = csv.writer(output_file)
    writer.writerow(['code', 'twilight_start', 'sunrise', 'sunset', 'twilight_end'])
    for row in reader:
        code = row['code']
        if code == 'NULL':
            continue
        lat = row['lat']
        lon = row['lon']
        sun_times = get_sun_times(lat, lon)
        writer.writerow([
            code,
            format_time(sun_times['civil_twilight_begin']),
            format_time(sun_times['sunrise']),
            format_time(sun_times['sunset']),
            format_time(sun_times['civil_twilight_end'])
        ])
