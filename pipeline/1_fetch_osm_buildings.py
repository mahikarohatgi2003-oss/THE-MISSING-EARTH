"""
Step 1 — Pull every mapped building footprint in the study area from
OpenStreetMap (via the Overpass API, wrapped by OSMnx). Free, no key.
"""
import os
import osmnx as ox
import geopandas as gpd

import config


def get_area_polygon():
    if config.BBOX:
        from shapely.geometry import box
        south, west, north, east = config.BBOX
        return gpd.GeoDataFrame(
            geometry=[box(west, south, east, north)], crs="EPSG:4326"
        )
    gdf = ox.geocode_to_gdf(config.PLACE_NAME)
    return gdf


def fetch_osm_buildings():
    print(f"Resolving study area: {config.PLACE_NAME if not config.BBOX else config.BBOX}")
    area = get_area_polygon()
    polygon = area.geometry.iloc[0]

    print("Querying Overpass for building footprints (this can take a minute)...")
    buildings = ox.features_from_polygon(polygon, tags={"building": True})

    # Keep only polygonal footprints, drop nodes tagged building=* etc.
    buildings = buildings[buildings.geometry.type.isin(["Polygon", "MultiPolygon"])]
    buildings = buildings[["geometry"]].reset_index(drop=True)
    buildings["source"] = "osm"

    os.makedirs(os.path.dirname(config.RAW_OSM_PATH), exist_ok=True)
    buildings.to_file(config.RAW_OSM_PATH, driver="GeoJSON")

    print(f"✓ {len(buildings)} OSM buildings saved → {config.RAW_OSM_PATH}")
    return buildings


if __name__ == "__main__":
    fetch_osm_buildings()
