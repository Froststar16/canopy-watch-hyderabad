"""
Data loading and caching for the Canopy Watch dashboard.

Column names across outputs/*.csv were set in earlier notebooks and aren't
all confirmed here. _resolve_col() tries a list of likely names per field
and raises a clear error (listing the columns it actually found) instead
of failing on a cryptic KeyError. If a field consistently fails to
resolve, add the real column name to the relevant *_CANDIDATES list below
— that's a one-line fix, not a rewrite.
"""

from __future__ import annotations
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUTS_DIR = ROOT_DIR / "outputs"

# --- column name candidates, first match in the file wins -----------------
# Confirmed against the actual outputs/*.csv headers. The KML's ward-ID
# field ("ward") is the one exception still unconfirmed against a real
# file — kept as a fallback candidate.
WARD_ID_CANDIDATES = ["ward_no", "Ward_No", "WARD_NO", "ward_number", "ward"]
WARD_NAME_CANDIDATES = ["ward_name", "Ward_Name", "WardName", "Name", "NAME"]
YEAR_CANDIDATES = ["year", "Year"]
NDVI_CANDIDATES = ["mean_ndvi", "ndvi_mean", "ndvi", "NDVI"]
LST_CANDIDATES = ["mean_lst_c", "lst_celsius", "lst_c", "lst", "LST_C"]
NDVI_CHANGE_CANDIDATES = ["ndvi_change", "ndvi_delta"]
LST_CHANGE_CANDIDATES = ["lst_change_c", "lst_change", "lst_delta_c"]
HEAT_RISK_CANDIDATES = ["heat_risk_score", "heat_risk", "risk_score"]
TREE_PROB_CANDIDATES = ["mean_tree_prob", "tree_prob_mean", "trees_prob_mean", "tree_probability"]
TREE_PROB_CHANGE_CANDIDATES = ["tree_prob_change", "trees_prob_change", "tree_cover_change"]


def _resolve_col(df: pd.DataFrame, candidates: list[str], field_label: str) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    raise KeyError(
        f"Couldn't find a column for '{field_label}'. Tried {candidates}. "
        f"Actual columns in this file: {list(df.columns)}. "
        f"Add the real name to the matching *_CANDIDATES list in data_loader.py."
    )


def _standardize(df: pd.DataFrame, mapping: dict[str, list[str]]) -> pd.DataFrame:
    """mapping: {standard_name: candidates_list}. Renames columns in place."""
    rename = {}
    for standard, candidates in mapping.items():
        rename[_resolve_col(df, candidates, standard)] = standard
    return df.rename(columns=rename)


def _clean_ward_id(series: pd.Series) -> pd.Series:
    """Normalizes ward_no to a plain string ('115', not '115.0'). KML/GIS
    exports often parse integer-like fields as float; CSVs from the
    notebooks don't. Without this, a KML ward '115.0' silently fails to
    join against a CSV ward '115' and the row just vanishes."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all():
        return numeric.astype(int).astype(str)
    return series.astype(str).str.strip()


def _extract_kml_ward_no(raw) -> str:
    """The real KML's ward field combines number and name in one string,
    e.g. '127-RANGAREDDY NAGAR' — confirmed against the actual file, not
    guessed. The 5 wards with no formal ward number (Bandla Guda,
    Cantonment Area, etc.) are just the bare place name with no prefix.
    Split on the first hyphen only when the prefix is numeric, so
    hyphenated place names like '138-MOULA-ALI' don't break."""
    text = str(raw).strip()
    if "-" in text:
        prefix, _, _rest = text.partition("-")
        if prefix.strip().isdigit():
            return prefix.strip()
    return text


def _ward_name_lookup(ndvi: pd.DataFrame) -> pd.DataFrame:
    """The KML's own name field is unconfirmed/unreliable; Phase 2's NDVI
    output covers all 155 wards with clean names, so it's the single
    source of truth for ward_name everywhere downstream — avoids two
    different 'ward_name' columns colliding on later merges.

    5 wards (annexed gram panchayats / institutional areas — Bandla Guda,
    Cantonment Area, Grampanchayat Peerzadi Guda, Kalavancha Gram
    Panchayath, OU) have no numeric ward_no in the source GIS data at
    all — their ward_no *is* the place name, and ward_name is null. Don't
    dropna() here or these 5 silently disappear from the whole app,
    contradicting the "show all 155 wards" scope decision. Falling back
    to ward_no as the display name is fine — it's already the place name.
    """
    lookup = ndvi[["ward_no", "ward_name"]].drop_duplicates("ward_no").reset_index(drop=True)
    lookup["ward_name"] = lookup["ward_name"].fillna(lookup["ward_no"])
    return lookup


@st.cache_data
def load_ward_boundaries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DATA_DIR / "ghmc_wards.kml", driver="KML")
    gdf = _standardize(gdf, {"ward_no": WARD_ID_CANDIDATES})
    gdf["ward_no"] = gdf["ward_no"].apply(_extract_kml_ward_no)
    gdf["ward_no"] = _clean_ward_id(gdf["ward_no"])
    ndvi = load_ndvi_by_ward()
    gdf = gdf[["ward_no", "geometry"]].merge(_ward_name_lookup(ndvi), on="ward_no", how="left")
    return gdf[["ward_no", "ward_name", "geometry"]]


@st.cache_data
def load_ndvi_by_ward() -> pd.DataFrame:
    df = pd.read_csv(OUTPUTS_DIR / "hyderabad_ndvi_by_ward.csv")
    df = _standardize(df, {
        "ward_no": WARD_ID_CANDIDATES,
        "year": YEAR_CANDIDATES,
        "ndvi": NDVI_CANDIDATES,
    })
    df["ward_no"] = _clean_ward_id(df["ward_no"])
    return df


@st.cache_data
def load_lst_by_ward() -> pd.DataFrame:
    df = pd.read_csv(OUTPUTS_DIR / "hyderabad_lst_by_ward.csv")
    df = _standardize(df, {
        "ward_no": WARD_ID_CANDIDATES,
        "year": YEAR_CANDIDATES,
        "lst_c": LST_CANDIDATES,
    })
    df["ward_no"] = _clean_ward_id(df["ward_no"])
    return df


@st.cache_data
def load_treecover_by_ward() -> pd.DataFrame:
    df = pd.read_csv(OUTPUTS_DIR / "hyderabad_treecover_dynamicworld_by_ward.csv")
    df = _standardize(df, {
        "ward_no": WARD_ID_CANDIDATES,
        "year": YEAR_CANDIDATES,
        "tree_prob": TREE_PROB_CANDIDATES,
    })
    df["ward_no"] = _clean_ward_id(df["ward_no"])
    return df


@st.cache_data
def load_heat_risk() -> pd.DataFrame:
    df = pd.read_csv(OUTPUTS_DIR / "hyderabad_heat_risk_wards.csv")
    df = _standardize(df, {
        "ward_no": WARD_ID_CANDIDATES,
        "ndvi_change": NDVI_CHANGE_CANDIDATES,
        "lst_change_c": LST_CHANGE_CANDIDATES,
        "heat_risk_score": HEAT_RISK_CANDIDATES,
    })
    df["ward_no"] = _clean_ward_id(df["ward_no"])
    return df


@st.cache_data
def load_cross_check() -> pd.DataFrame:
    df = pd.read_csv(OUTPUTS_DIR / "hyderabad_heat_risk_treecover_cross_check.csv")
    df = _standardize(df, {
        "ward_no": WARD_ID_CANDIDATES,
        "tree_prob_change": TREE_PROB_CHANGE_CANDIDATES,
        "heat_risk_score": HEAT_RISK_CANDIDATES,
    })
    df["ward_no"] = _clean_ward_id(df["ward_no"])
    return df


@st.cache_data
def load_all() -> dict:
    """Single entry point app.py calls. Returns every dataframe plus a
    ward-geometry GeoDataFrame merged with heat-risk + cross-check metrics,
    ready for the choropleth."""
    wards = load_ward_boundaries()
    ndvi = load_ndvi_by_ward()
    lst = load_lst_by_ward()
    treecover = load_treecover_by_ward()
    heat_risk = load_heat_risk()
    cross_check = load_cross_check()

    # left-join on the full 155-ward boundary so every ward renders on the
    # map — missing metrics come through as NaN rather than dropped rows.
    # Only pull heat_risk's metric columns (not its own ward_name/zone,
    # which would otherwise collide with wards' ward_name on merge).
    map_gdf = wards.merge(
        heat_risk[["ward_no", "ndvi_change", "lst_change_c", "heat_risk_score"]],
        on="ward_no",
        how="left",
    )
    map_gdf = map_gdf.merge(
        cross_check[["ward_no", "tree_prob_change"]], on="ward_no", how="left"
    )

    return {
        "wards": wards,
        "ndvi": ndvi,
        "lst": lst,
        "treecover": treecover,
        "heat_risk": heat_risk,
        "cross_check": cross_check,
        "map_gdf": map_gdf,
    }
