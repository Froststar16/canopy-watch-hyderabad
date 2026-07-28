# Canopy Watch — Hyderabad

Tracking tree canopy / green cover change across Hyderabad using satellite NDVI and land surface
temperature data, ward by ward — checked against Telangana's Haritha Haram afforestation claims.

## Why this project

Telangana's Haritha Haram program (launched 2015) reports large gains in green cover, but sapling
survival rates were never systematically tracked. This project independently measures actual
canopy change using satellite data — vegetation index (NDVI) trends over time, correlated with
land surface temperature (LST) to quantify local climate impact — and (optionally) checks it
against publicly reported plantation data.

## Boundary data

Ward boundaries: [OpenCity India — Hyderabad Wards Info](https://data.opencity.in/dataset/hyderabad-wards-info),
sourced from GHMC's own GIS. The live dataset currently has 155 ward features. GHMC is also
mid-way through a High Court-mandated delimitation that will eventually take it to 300 wards —
this project uses the current, legally-in-force ward set and will move to the 300-ward layout
once that's published as open data.

The citywide boundary used for analysis is the dissolved union of these 155 wards, rather than
GHMC's separately-published boundary layer, which has a geometry Earth Engine won't ingest.

## Results so far

**Phase 1 (MVP) — mean NDVI, 2016–present, placeholder bounding-box AOI:**

![NDVI trend for Hyderabad, 2016–present](outputs/ndvi_trend.png)

Raw values: [`outputs/hyderabad_ndvi_yearly.csv`](outputs/hyderabad_ndvi_yearly.csv)

> Note: this run uses a rough bounding box around Hyderabad/GHMC, not the actual city boundary —
> treat it as a pipeline sanity check rather than a final result. Phase 2 (real GHMC boundary +
> ward-level breakdown) refines this below.

**Phase 2 — real GHMC boundary, ward-level NDVI, 2016–present:**

![NDVI trend for Hyderabad, real GHMC boundary](outputs/ndvi_trend_realboundary.png)

Citywide (real boundary): [`outputs/hyderabad_ndvi_yearly_realboundary.csv`](outputs/hyderabad_ndvi_yearly_realboundary.csv)
Per-ward, year × ward long format: [`outputs/hyderabad_ndvi_by_ward.csv`](outputs/hyderabad_ndvi_by_ward.csv)

![Biggest ward-level NDVI gains and losses](outputs/ward_ndvi_change.png)

> The Phase 1 placeholder bounding box included a meaningful amount of non-GHMC area — the
> real-boundary citywide trend above is the first result that reflects the actual city extent.

**Phase 3 — land surface temperature (LST) + NDVI/heat correlation, 2016–present:**

Ward-level LST: [`outputs/hyderabad_lst_by_ward.csv`](outputs/hyderabad_lst_by_ward.csv)
Merged NDVI + LST table: [`outputs/hyderabad_ndvi_lst_by_ward.csv`](outputs/hyderabad_ndvi_lst_by_ward.csv)

![NDVI vs LST across all wards, all years](outputs/ndvi_lst_scatter.png)

The scatter plot's title reports the Pearson correlation between ward-level NDVI and LST across
every ward-year in the dataset — the core urban-heat-island signal this project set out to
measure. A negative slope means greener wards run measurably cooler.

Heat-risk shortlist — wards where canopy declined *and* temperature rose the most, first year vs.
most recent: [`outputs/hyderabad_heat_risk_wards.csv`](outputs/hyderabad_heat_risk_wards.csv)

![Top 15 heat-risk wards: canopy loss vs. temperature rise](outputs/ward_heat_risk.png)

> LST is computed from Landsat 8/9 thermal data at 30 m resolution, vs. NDVI's 10 m (Sentinel-2) —
> ward-level averages are still directly comparable, but the two aren't pixel-for-pixel aligned.

## Stack

- **Google Earth Engine (Python API)** — all satellite computation runs server-side on Google's
  infrastructure. You never download raw scene imagery; you query aggregated results (a mean
  NDVI/LST value for a region-year, a small exported PNG/GeoTIFF). This is why the project is
  Colab-friendly with minimal storage use.
- **Google Colab** — free compute, no local setup. Mount Google Drive for persistent storage of
  outputs between sessions (Colab's local disk is wiped when the runtime disconnects).
- **geemap** — adds interactive map display and easier GEE→pandas/matplotlib workflows on top of
  the raw `earthengine-api`.
- **geopandas + shapely** (from Phase 2) — loading, cleaning, and repairing the real ward/boundary
  geometries before they go into Earth Engine.
- **scipy** (from Phase 3) — Pearson correlation between ward-level NDVI and LST.
- **Streamlit + Folium/leafmap** (later phase) — dashboard layer.

## Storage strategy

- Raw Sentinel-2/Landsat imagery: **never downloaded**. GEE queries return aggregated stats only.
- Outputs saved to Drive (`/content/drive/MyDrive/canopy-watch-hyderabad/outputs/`): CSVs (time
  series), PNGs (charts/thumbnails), occasional small clipped GeoTIFFs for dashboard visuals (tens
  of MB, not GB).
- Ward/boundary source files saved to Drive
  (`/content/drive/MyDrive/canopy-watch-hyderabad/data/`): small KML files (a few MB at most).
- Only code, small CSVs, KMLs, and PNGs get pushed to GitHub. Anything in `outputs/*.tif` is
  gitignored — keep those in Drive only.

## Setup

1. Register for Earth Engine access: https://signup.earthengine.google.com (non-commercial/research use).
   - If your Google account is a managed school account with restricted Cloud project creation or
     third-party OAuth, register with a personal Gmail instead. You can still mount your school
     Drive in the same Colab notebook — they're independent auth flows.
2. Open `notebooks/01_setup_ndvi_pipeline.ipynb` in Google Colab (upload it, or open directly from
   GitHub via Colab's "Open notebook → GitHub" tab once this repo is pushed).
3. Run the notebook top to bottom. It will prompt you to authenticate with Earth Engine
   (`ee.Authenticate()`) and mount Drive.
4. Replace the placeholder `PROJECT_ID` in the `ee.Initialize()` call with the Cloud project ID you
   get during Earth Engine registration (this project uses `canopy-watch-hyderabad`).
5. Then run `notebooks/02_ward_level_ndvi.ipynb` — it downloads the real GHMC ward boundaries
   automatically, replacing the Phase 1 placeholder bounding box, and produces the ward-level NDVI
   breakdown.
6. Then run `notebooks/03_lst_correlation.ipynb` — it reloads the same ward boundaries, computes
   yearly land surface temperature per ward from Landsat 8/9, merges it with the Phase 2 NDVI
   table, and produces the NDVI/LST correlation and heat-risk outputs above.

## Roadmap

- **✅ Phase 1 — Setup + NDVI MVP** (`01_setup_ndvi_pipeline.ipynb`): auth, rough AOI, yearly mean
  NDVI trend for Hyderabad, 2016–present.
- **✅ Phase 2 — Real boundary + ward-level breakdown** (`02_ward_level_ndvi.ipynb`): sourced the
  actual GHMC ward boundaries (155 wards, GHMC's own GIS via OpenCity India), re-ran NDVI against
  the real city extent, and computed yearly mean NDVI per ward.
- **✅ Phase 3 — Climate correlation** (`03_lst_correlation.ipynb`): computed yearly land surface
  temperature per ward from Landsat 8/9 thermal data, correlated it against ward-level NDVI, and
  produced a heat-risk shortlist of wards with the worst combined canopy-loss/temperature-rise trend.
- **Phase 4 — Accountability overlay (optional)**: source public Haritha Haram sapling-count data
  (state reports / RTI), compare self-reported plantation numbers against satellite-measured
  canopy trend per area — cross-check specifically against the Phase 3 heat-risk wards.
- **Phase 5 — Dashboard**: Streamlit + Folium/leafmap app — select an area, see its NDVI trend,
  LST trend, and any linked plantation data.

## Repo structure

```
canopy-watch-hyderabad/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── ghmc_wards.kml
│   └── ghmc_boundary.kml
├── notebooks/
│   ├── 01_setup_ndvi_pipeline.ipynb
│   ├── 02_ward_level_ndvi.ipynb
│   └── 03_lst_correlation.ipynb
└── outputs/
    ├── hyderabad_ndvi_yearly.csv
    ├── ndvi_trend.png
    ├── hyderabad_ndvi_yearly_realboundary.csv
    ├── ndvi_trend_realboundary.png
    ├── hyderabad_ndvi_by_ward.csv
    ├── ward_ndvi_change.png
    ├── hyderabad_lst_by_ward.csv
    ├── hyderabad_ndvi_lst_by_ward.csv
    ├── ndvi_lst_scatter.png
    ├── hyderabad_heat_risk_wards.csv
    └── ward_heat_risk.png
```
