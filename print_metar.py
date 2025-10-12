import urllib.request
import xml.etree.ElementTree as ET
import csv

# Path to your airports file
AIRPORTS_CSV = "airports.csv"
TIMEZONE_LOOKBACK_HOURS = 5  # same as your main script
OUTPUT_FILE = "metar_raw_output.txt"  # optional: set to None to only print

def fetch_metars(airport_ids, hours=5):
    ids = ",".join([a for a in airport_ids if a != "NULL"])
    url = f"https://aviationweather.gov/api/data/metar?ids={ids}&hours={hours}&format=xml"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'METARMap/RawPrinter/1.0'}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()

def main():
    # Load airport codes
    airports = []
    with open(AIRPORTS_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('code'):
                airports.append(row['code'].strip())

    # Fetch XML from API
    print("Fetching METAR data...")
    xml_data = fetch_metars(airports, hours=TIMEZONE_LOOKBACK_HOURS)
    root = ET.fromstring(xml_data)

    # Extract and print raw_text for every station
    print("Printing all METAR raw_text entries:\n")
    lines = []
    for metar in root.iter('METAR'):
        sid = metar.find('station_id').text if metar.find('station_id') is not None else "UNKNOWN"
        raw = metar.find('raw_text').text if metar.find('raw_text') is not None else ""
        line = f"{sid}: {raw}"
        print(line)
        lines.append(line)

    # Optional: write to file for later inspection
    if OUTPUT_FILE:
        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(lines))
        print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
