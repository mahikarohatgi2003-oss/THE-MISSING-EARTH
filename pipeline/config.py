"""
Everything you'd want to tweak lives here — nowhere else.

Pick a district by name (Nominatim-resolvable) OR give it a bounding box
directly if the name lookup is ambiguous.
"""

# --- Study area -------------------------------------------------------
# Any string OSMnx / Nominatim can geocode. Be specific to avoid picking
# the wrong "Gurugram" in the world.
PLACE_NAME = "Sohna, Gurugram District, Haryana, India"

# Optional: set this to override PLACE_NAME with an explicit bbox
# (south, west, north, east). Leave as None to geocode PLACE_NAME instead.
BBOX = None  # e.g. (28.20, 77.05, 28.30, 77.15)

# --- Matching parameters -----------------------------------------------
# How close an AI-detected footprint must be to an OSM footprint (in
# metres) to be considered "already mapped". Buildings closer than this
# to any OSM building are marked mapped; farther than this = missing.
MATCH_BUFFER_METERS = 5

# Minimum footprint area (m^2) to count as a real building, filters out
# noise/false positives from the AI dataset.
MIN_BUILDING_AREA_M2 = 9

# --- Heatmap grid --------------------------------------------------------
HEATMAP_CELL_SIZE_METERS = 250

# --- Volunteer estimate --------------------------------------------------
# Buildings traced per mapper-hour on a validated HOT Tasking Manager
# project (published HOT throughput figures land in the 30-60/hr range).
BUILDINGS_PER_MAPPER_HOUR = 40
HOURS_PER_MAPATHON_SESSION = 3

# --- Output paths ----------------------------------------------------------
RAW_OSM_PATH = "data/osm_buildings.geojson"
RAW_AI_PATH = "data/ai_buildings.geojson"
SITE_DATA_DIR = "docs/data"
