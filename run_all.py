"""
Runs the full pipeline end to end: OSM fetch → AI buildings fetch →
comparison → heatmap → volunteer estimate. Edit config.py first.
"""
import sys
import os
from importlib import import_module

sys.path.insert(0, os.path.dirname(__file__))


def main():
    steps = [
        ("1_fetch_osm_buildings", "fetch_osm_buildings"),
        ("2_fetch_ai_buildings", "fetch_ai_buildings"),
        ("3_compare_buildings", "compare_buildings"),
        ("4_generate_heatmap", "generate_heatmap"),
        ("5_estimate_volunteers", "estimate_volunteers"),
    ]

    for i, (module_name, func_name) in enumerate(steps, start=1):
        print(f"\n{'=' * 60}\nSTEP {i}/{len(steps)}: {module_name}\n{'=' * 60}")
        mod = import_module(module_name)
        getattr(mod, func_name)()

    print("\n✓ Pipeline complete. Commit docs/data/*.geojson and docs/data/stats.json,")
    print("  push to GitHub, and enable Pages on the /docs folder.")


if __name__ == "__main__":
    main()
