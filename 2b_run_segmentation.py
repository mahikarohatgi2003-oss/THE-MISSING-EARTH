"""
Step 2b (OPTIONAL, full path) — The literal "download Sentinel-2 imagery,
run an AI model" workflow, for when you want to demo real inference
instead of using Microsoft's pre-computed footprints.

Pulls a cloud-free Sentinel-2 scene from Microsoft's Planetary Computer
(free, no key), then runs Meta's Segment Anything Model over it via the
`segment-geospatial` wrapper to extract building-shaped polygons.

This is heavier: expect several GB of RAM/VRAM use and a few minutes per
tile even on CPU. Output schema matches 2_fetch_ai_buildings.py exactly,
so you can swap this in as a drop-in replacement.

    pip install segment-geospatial planetary-computer pystac-client rasterio

Then:
    python pipeline/2b_run_segmentation.py
"""
import os
import geopandas as gpd
import planetary_computer
import pystac_client
from importlib import import_module

import config

fetch_osm = import_module("1_fetch_osm_buildings")


def fetch_sentinel2_scene(area_gdf):
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    bbox = area_gdf.total_bounds.tolist()  # [minx, miny, maxx, maxy]

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        query={"eo:cloud_cover": {"lt": 10}},
        sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
        limit=5,
    )
    items = list(search.items())
    if not items:
        raise RuntimeError("No low-cloud Sentinel-2 scenes found for this area/date range.")

    item = items[0]
    print(f"Using Sentinel-2 scene {item.id} ({item.properties['eo:cloud_cover']}% cloud)")
    # True-color visual asset, already pan-sharpened to 10m
    return item.assets["visual"].href


def run_segmentation():
    from samgeo import SamGeo

    area = fetch_osm.get_area_polygon()
    image_url = fetch_sentinel2_scene(area)

    os.makedirs("data/imagery", exist_ok=True)
    local_tif = "data/imagery/sentinel2_scene.tif"

    print("Downloading Sentinel-2 visual band (COG, windowed to study area)...")
    import rioxarray
    da = rioxarray.open_rasterio(image_url, masked=True)
    minx, miny, maxx, maxy = area.to_crs(da.rio.crs).total_bounds
    da_clip = da.rio.clip_box(minx, miny, maxx, maxy)
    da_clip.rio.to_raster(local_tif)

    print("Running Segment Anything Model over the scene...")
    sam = SamGeo(model_type="vit_b", automatic=True, sam_kwargs=None)
    sam.generate(local_tif, output="data/imagery/segments.tif", foreground=True)
    sam.tiff_to_vector("data/imagery/segments.tif", config.RAW_AI_PATH)

    gdf = gpd.read_file(config.RAW_AI_PATH)
    gdf_m = gdf.to_crs(gdf.estimate_utm_crs())
    gdf = gdf[
        (gdf_m.geometry.area >= config.MIN_BUILDING_AREA_M2)
        & (gdf_m.geometry.area <= 2000)  # drop scene-scale blobs (roads, fields)
    ].reset_index(drop=True)
    gdf["source"] = "ai_detected_sam"
    gdf.to_file(config.RAW_AI_PATH, driver="GeoJSON")

    print(f"✓ {len(gdf)} AI-segmented candidate buildings saved → {config.RAW_AI_PATH}")
    print("  Note: raw SAM output over satellite imagery is noisier than the")
    print("  Microsoft pretrained footprints — expect to raise MIN/MAX area")
    print("  thresholds in config.py and re-run step 3 to tune precision.")


if __name__ == "__main__":
    run_segmentation()
