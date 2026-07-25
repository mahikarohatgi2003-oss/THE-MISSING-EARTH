"""
Step 2 (fast path) — Pull AI-detected building footprints for the study
area from Microsoft's Global ML Building Footprints dataset, hosted
free (no API key) on the Microsoft Planetary Computer.

These footprints were produced by Microsoft running a segmentation model
over Bing/Maxar satellite imagery — this IS the "AI model detects
buildings from imagery" step, already done at country scale, so you get
it for free instead of training/running your own network.

If you specifically want to run your own model on raw Sentinel-2 tiles,
use 2b_run_segmentation.py instead — same output schema, drop-in
replacement for this script.
"""
import os
import json
import requests
import geopandas as gpd
from shapely.geometry import shape

import config
from importlib import import_module

fetch_osm = import_module("1_fetch_osm_buildings")

DATASET_LINKS = "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv"


def get_quad_keys_for_bbox(minx, miny, maxx, maxy, zoom=9):
    """Microsoft's dataset is tiled by Bing quadkey. Compute which tiles
    our bounding box touches."""
    import mercantile
    tiles = list(mercantile.tiles(minx, miny, maxx, maxy, zoom))
    return {mercantile.quadkey(t) for t in tiles}


def fetch_ai_buildings():
    import pandas as pd

    area = fetch_osm.get_area_polygon()
    minx, miny, maxx, maxy = area.total_bounds

    print("Looking up Microsoft building-footprint tiles for this area...")
    quadkeys = get_quad_keys_for_bbox(minx, miny, maxx, maxy)

    links_df = pd.read_csv(DATASET_LINKS)
    links_df["QuadKey"] = links_df["QuadKey"].astype(str)
    rows = links_df[links_df["QuadKey"].isin(quadkeys)]

    if rows.empty:
        raise RuntimeError(
            "No Microsoft footprint tiles found for this area/country. "
            "Check that PLACE_NAME/BBOX in config.py is correct, or fall "
            "back to pipeline/2b_run_segmentation.py."
        )

    all_geoms = []
    for _, row in rows.iterrows():
        print(f"Downloading tile for quadkey {row['QuadKey']} "
              f"({row['Location']})...")
        r = requests.get(row["Url"], stream=True, timeout=120)
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            feat = json.loads(line)
            geom = shape(feat["geometry"])
            if geom.is_valid and not geom.is_empty:
                all_geoms.append(geom)

    gdf = gpd.GeoDataFrame(geometry=all_geoms, crs="EPSG:4326")
    # Clip to exact study-area polygon, not just the bbox
    gdf = gpd.clip(gdf, area)

    # Drop tiny slivers / noise
    gdf_m = gdf.to_crs(gdf.estimate_utm_crs())
    gdf = gdf[gdf_m.geometry.area >= config.MIN_BUILDING_AREA_M2].reset_index(drop=True)
    gdf["source"] = "ai_detected"

    os.makedirs(os.path.dirname(config.RAW_AI_PATH), exist_ok=True)
    gdf.to_file(config.RAW_AI_PATH, driver="GeoJSON")

    print(f"✓ {len(gdf)} AI-detected buildings saved → {config.RAW_AI_PATH}")
    return gdf


if __name__ == "__main__":
    fetch_ai_buildings()
