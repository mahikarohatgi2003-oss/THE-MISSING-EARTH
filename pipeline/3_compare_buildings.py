"""
Step 3 — Spatially compare AI-detected buildings against OSM buildings.

For every AI-detected footprint:
  - if its centroid falls within MATCH_BUFFER_METERS of any OSM building
    → status = "mapped" (OSM already has this one)
  - otherwise → status = "missing" (likely un-mapped building)

Output: docs/data/mapped.geojson, docs/data/missing.geojson, plus a
combined docs/data/comparison.geojson for anyone who wants raw access.
"""
import os
import geopandas as gpd

import config


def compare_buildings():
    osm = gpd.read_file(config.RAW_OSM_PATH)
    ai = gpd.read_file(config.RAW_AI_PATH)

    utm_crs = ai.estimate_utm_crs()
    osm_m = osm.to_crs(utm_crs)
    ai_m = ai.to_crs(utm_crs)

    osm_union = osm_m.geometry.buffer(config.MATCH_BUFFER_METERS).union_all()

    ai_m["centroid"] = ai_m.geometry.centroid
    ai_m["status"] = ai_m["centroid"].apply(
        lambda pt: "mapped" if osm_union.contains(pt) else "missing"
    )

    result = ai.copy()
    result["status"] = ai_m["status"].values

    os.makedirs(config.SITE_DATA_DIR, exist_ok=True)

    mapped = result[result.status == "mapped"].drop(columns=[c for c in ["source"] if c in result.columns])
    missing = result[result.status == "missing"].drop(columns=[c for c in ["source"] if c in result.columns])

    mapped.to_file(f"{config.SITE_DATA_DIR}/mapped.geojson", driver="GeoJSON")
    missing.to_file(f"{config.SITE_DATA_DIR}/missing.geojson", driver="GeoJSON")
    result.to_file(f"{config.SITE_DATA_DIR}/comparison.geojson", driver="GeoJSON")

    print(f"✓ {len(mapped)} already mapped, {len(missing)} likely missing")
    print(f"  → {config.SITE_DATA_DIR}/mapped.geojson")
    print(f"  → {config.SITE_DATA_DIR}/missing.geojson")

    return mapped, missing


if __name__ == "__main__":
    compare_buildings()
