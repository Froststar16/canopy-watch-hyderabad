# Canopy Watch — Hyderabad

Tracking green cover change and its local climate impact across Hyderabad/GHMC, and checking it against the official Haritha Haram afforestation narrative.

## Why this project

Telangana's Haritha Haram program (launched 2015) reports large gains in green cover, but sapling survival rates were never systematically tracked. This project independently measures actual canopy change using satellite data — vegetation index (NDVI) trends over time, correlated with land surface temperature (LST) to quantify local climate impact — and (optionally) checks it against publicly reported plantation data.

## Stack

- **Google Earth Engine (Python API)** — all satellite computation runs server-side on Google's infrastructure. You never download raw scene imagery; you query aggregated results (a mean NDVI value for a region-year, a small exported PNG/GeoTIFF). This is why the project is Colab-friendly with minimal storage use.
- **Google Colab** — free compute, no local setup. Mount Google Drive for persistent storage of outputs between sessions (Colab's local disk is wiped when the runtime disconnects).
- **geemap** — adds interactive map display and easier GEE→pandas/matplotlib workflows on top of the raw `earthengine-api`.
- **Streamlit + Folium/leafmap** (later phase) — dashboard layer.

## Storage strategy

- Raw Sentinel-2/Landsat imagery: **never downloaded**. GEE queries return aggregated stats only.
- Outputs saved to Drive (`/content/drive/MyDrive/canopy-watch-hyderabad/outputs/`): CSVs (time series), PNGs (charts/thumbnails), occasional small clipped GeoTIFFs for dashboard visuals (tens of MB, not GB).
- Only code, small CSVs, and PNGs get pushed to GitHub. Anything in `outputs/*.tif` is gitignored — keep those in Drive only.

## Setup

1. Register for Earth Engine access: https://signup.earthengine.google.com (non-commercial/research use).
   - If your Google account is a managed school account with restricted Cloud project creation or third-party OAuth, register with a personal Gmail instead. You can still mount your school Drive in the same Colab notebook — they're independent auth flows.
2. Open `notebooks/01_setup_ndvi_pipeline.ipynb` in Google Colab (upload it, or open directly from GitHub via Colab's "Open notebook → GitHub" tab once this repo is pushed).
3. Run the notebook top to bottom. It will prompt you to authenticate with Earth Engine (`ee.Authenticate()`) and mount Drive.
4. Replace the placeholder `PROJECT_ID` in the `ee.Initialize()` call with the Cloud project ID you get during Earth Engine registration.
5. Replace the placeholder bounding-box AOI with an actual GHMC boundary once you've sourced one (see Roadmap, Phase 2).

## Roadmap

- **Phase 1 — Setup + NDVI MVP** (`01_setup_ndvi_pipeline.ipynb`): auth, rough AOI, yearly mean NDVI trend for Hyderabad, 2016–present.
- **Phase 2 — Real boundary + ward-level breakdown**: source an actual GHMC/ward shapefile (Telangana State GIS portal, OpenStreetMap via Overpass Turbo, or Data{Meet}/OpenCity India), rerun NDVI per ward to localize hotspots.
- **Phase 3 — Climate correlation**: pull Landsat thermal band, compute land surface temperature (LST), correlate against NDVI trend per area (urban heat island analysis).
- **Phase 4 — Accountability overlay (optional)**: source public Haritha Haram sapling-count data (state reports / RTI), compare self-reported plantation numbers against satellite-measured canopy trend per area.
- **Phase 5 — Dashboard**: Streamlit + Folium/leafmap app — select an area, see its NDVI trend, LST trend, and any linked plantation data.

## Repo structure

```
canopy-watch-hyderabad/
├── README.md
├── requirements.txt
├── .gitignore
└── notebooks/
    └── 01_setup_ndvi_pipeline.ipynb
```
