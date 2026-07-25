"""
Step 4 — Turn the "missing" buildings into a grid-cell density heatmap,
so mapping coordinators can see at a glance which neighbourhoods need
attention rather than scanning individual points.
"""
import os
import numpy as np
import geopandas as gpd
from shapely.geometry import box

import config


def generate_heatmap():
    missing = gpd.read_file(f"{config.SITE_DATA_DIR}/missing.geojson")
    if missing.empty:
        print("No missing buildings found — skipping heatmap (nothing to show).")
        return

    utm = missing.estimate_utm_crs()
    missing_m = missing.to_crs(utm)

    minx, miny, maxx, maxy = missing_m.total_bounds
    cell = config.HEATMAP_CELL_SIZE_METERS

    xs = np.arange(minx, maxx + cell, cell)
    ys = np.arange(miny, maxy + cell, cell)

    cells = []
    for x in xs[:-1]:
        for y in ys[:-1]:
            cells.append(box(x, y, x + cell, y + cell))

    grid = gpd.GeoDataFrame(geometry=cells, crs=utm)
    joined = gpd.sjoin(missing_m, grid, how="left", predicate="within")
    counts = joined.groupby("index_right").size()

    grid["missing_count"] = grid.index.map(counts).fillna(0).astype(int)
    grid = grid[grid.missing_count > 0].reset_index(drop=True)

    max_count = grid.missing_count.max()
    grid["intensity"] = (grid.missing_count / max_count).round(3)

    grid_wgs84 = grid.to_crs("EPSG:4326")
    grid_wgs84.to_file(f"{config.SITE_DATA_DIR}/heatmap.geojson", driver="GeoJSON")

    print(f"✓ Heatmap grid ({len(grid)} cells, {cell}m each) → "
          f"{config.SITE_DATA_DIR}/heatmap.geojson")
    print(f"  Hottest cell: {max_count} missing buildings in one {cell}x{cell}m cell")


if __name__ == "__main__":
    generate_heatmap()
