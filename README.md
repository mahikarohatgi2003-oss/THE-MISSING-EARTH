# 🛰️ The Missing Earth

**A workflow that finds the buildings OpenStreetMap doesn't know about yet.**

Pick a district → pull AI-detected building footprints from satellite imagery →
compare against OpenStreetMap → see exactly what's missing, where the gaps
cluster, and how many volunteer-hours it would take to close them.

Live output is a static, single-page **survey dashboard** (deployed via
**GitHub Pages**, no backend required) — a study-area panel, an AI-detection
scorecard, an OSM-comparison donut chart with a mini heatmap, the full
interactive Leaflet map, and a "suggested next edits" priority list. The
analysis pipeline is a set of Python scripts you run once (locally or in
Colab — both free) to generate the GeoJSON the dashboard reads.

**v1 scope is buildings only.** The dashboard's AI-detection panel also shows
"Missing roads," "Missing waterways," and "Land use gaps" cards, honestly
labeled **Roadmap** rather than filled with placeholder numbers — extending
`pipeline/` to compare OSM roads/waterways against Overpass, or land cover
against a dataset like ESA WorldCover, would light those up using the same
spatial-diff pattern as `3_compare_buildings.py`.

```
┌──────────────┐   ┌──────────────────┐   ┌───────────────┐   ┌────────────┐
│ OSM buildings│   │ AI-detected      │   │ Spatial diff  │   │ Heatmap +  │
│ (Overpass)   │ + │ buildings        │ → │ mapped vs.    │ → │ volunteer  │
│              │   │ (Sentinel-2 /    │   │ missing       │   │ estimate   │
│              │   │  MS/Google AI    │   │               │   │            │
│              │   │  footprints)     │   │               │   │            │
└──────────────┘   └──────────────────┘   └───────────────┘   └────────────┘
                                                    │
                                                    ▼
                                     docs/data/*.geojson → Leaflet map (GitHub Pages)
```

## Why it's honest about "AI detection"

There are two ways to get AI-detected building footprints, both free:

1. **Fast path (default, recommended):** Microsoft's [Global ML Building
   Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints) and
   Google's [Open Buildings](https://sites.research.google/open-buildings/)
   datasets are *already* the output of CNN/segmentation models run over
   satellite imagery, covering nearly all of India. `pipeline/2_fetch_ai_buildings.py`
   pulls the tile for your district straight from Microsoft's Planetary
   Computer STAC catalog. No GPU, no training, no imagery download needed.
2. **Full path (optional, `pipeline/2b_run_segmentation.py`):** if you want to
   *actually* run a segmentation model yourself over raw Sentinel-2 tiles, that
   script uses [`segment-geospatial`](https://github.com/opengeos/segment-geospatial)
   (Meta's Segment Anything Model, geospatial wrapper) against imagery pulled
   from Microsoft's Planetary Computer. This is slower and needs more RAM, but
   it's the literal "download Sentinel-2 → run AI model" workflow from your
   brief.

Both feed the same downstream comparison step, so start with path 1 and only
reach for path 2 if you specifically want to demo custom model inference.

## Repo layout

```
missing-earth/
├── pipeline/
│   ├── 1_fetch_osm_buildings.py     # OSM buildings for your district (Overpass)
│   ├── 2_fetch_ai_buildings.py      # AI-detected buildings (MS Planetary Computer)
│   ├── 2b_run_segmentation.py       # OPTIONAL: real SAM segmentation on Sentinel-2
│   ├── 3_compare_buildings.py       # Spatial diff → mapped / missing
│   ├── 4_generate_heatmap.py        # Grid density of missing buildings
│   ├── 5_estimate_volunteers.py     # Volunteer-hour estimate from HOT OSM edit rates
│   └── run_all.py                   # Runs 1 → 5 in order
├── data/                            # Raw pipeline output (gitignored except .gitkeep)
├── docs/                            # The GitHub Pages site (Leaflet frontend)
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── data/                        # Final GeoJSON the map reads (small, committed)
├── requirements.txt
└── .github/workflows/pages.yml      # Auto-deploys docs/ to GitHub Pages
```

## Quickstart

```bash
git clone https://github.com/<you>/missing-earth.git
cd missing-earth
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Edit the district in pipeline/config.py, then:
python pipeline/run_all.py
```

This writes `docs/data/mapped.geojson`, `docs/data/missing.geojson`,
`docs/data/heatmap.geojson`, and `docs/data/stats.json`. Commit those, push,
and the map is live.

## Deploying (GitHub Pages only — no server)

1. Push this repo to GitHub.
2. Repo **Settings → Pages → Source → Deploy from a branch → `main` / `docs`**.
   (The included workflow at `.github/workflows/pages.yml` does this
   automatically via Actions if you'd rather not touch a dropdown.)
3. Your map is live at `https://<you>.github.io/missing-earth/` in ~1 minute.

There is no backend, no API key, no server to pay for — the pipeline runs
once on your machine (or in a free Colab notebook, see
`pipeline/colab_notebook.md`), and the site is 100% static files reading
GeoJSON.

## Estimating volunteer effort

`5_estimate_volunteers.py` uses published HOT OSM tasking-manager throughput
(≈ 30–60 building traces per mapper-hour for a validated task, we default to
40) to turn "N buildings missing" into "≈ X volunteer-hours" and "≈ Y mappers
over a weekend mapathon," so this becomes something a local OSM community
chapter or HOT project lead could actually act on.

## Attribution / data sources (all free, no auth needed for the fast path)

- OpenStreetMap contributors — ODbL
- Microsoft Global ML Building Footprints — ODbL
- Sentinel-2 imagery — Copernicus (via Microsoft Planetary Computer, no key required)
- Segment Anything Model — Meta AI, Apache 2.0 (optional path only)
