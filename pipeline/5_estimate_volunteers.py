"""
Step 5 — Turn "N buildings missing" into an actionable effort estimate:
volunteer-hours, mapper-count for a weekend mapathon, and % coverage.
Writes docs/data/stats.json, which the frontend reads for the stat cards.
"""
import json
import math
import geopandas as gpd

import config


def estimate_volunteers():
    mapped = gpd.read_file(f"{config.SITE_DATA_DIR}/mapped.geojson")
    missing = gpd.read_file(f"{config.SITE_DATA_DIR}/missing.geojson")

    n_mapped = len(mapped)
    n_missing = len(missing)
    total = n_mapped + n_missing
    coverage_pct = round((n_mapped / total) * 100, 1) if total else 0.0

    hours_needed = n_missing / config.BUILDINGS_PER_MAPPER_HOUR
    mapathon_sessions = math.ceil(hours_needed / config.HOURS_PER_MAPATHON_SESSION) if n_missing else 0
    # mappers needed for a single weekend (2-session) mapathon
    mappers_for_one_weekend = math.ceil(hours_needed / (config.HOURS_PER_MAPATHON_SESSION * 2)) if n_missing else 0

    stats = {
        "place_name": config.PLACE_NAME,
        "buildings_mapped": n_mapped,
        "buildings_missing": n_missing,
        "buildings_total_detected": total,
        "coverage_pct": coverage_pct,
        "estimated_volunteer_hours": round(hours_needed, 1),
        "estimated_mapathon_sessions": mapathon_sessions,
        "estimated_mappers_for_one_weekend": mappers_for_one_weekend,
        "buildings_per_mapper_hour_assumed": config.BUILDINGS_PER_MAPPER_HOUR,
    }

    with open(f"{config.SITE_DATA_DIR}/stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("✓ Coverage summary:")
    print(f"  {coverage_pct}% mapped  ({n_mapped}/{total} buildings)")
    print(f"  ≈ {stats['estimated_volunteer_hours']}h of mapping to close the gap")
    print(f"  ≈ {mappers_for_one_weekend} volunteers for a single weekend mapathon")
    print(f"  → {config.SITE_DATA_DIR}/stats.json")

    return stats


if __name__ == "__main__":
    estimate_volunteers()
