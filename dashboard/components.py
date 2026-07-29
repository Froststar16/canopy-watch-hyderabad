"""Reusable UI pieces for the Canopy Watch dashboard."""

import pandas as pd
import streamlit as st

GLOSSARY = {
    "NDVI": (
        "Normalized Difference Vegetation Index — a 0 to 1 score from satellite imagery "
        "showing how much healthy green vegetation is in an area. Higher means more or "
        "healthier plant cover (trees, parks, farmland); lower means bare ground, "
        "concrete, or water."
    ),
    "LST (land surface temperature)": (
        "How hot the ground itself is, measured by satellite thermal sensors — not the "
        "air temperature you'd see in a weather forecast. Areas with less tree cover and "
        "more concrete tend to run hotter, sometimes called the 'urban heat island' effect."
    ),
    "Tree-cover probability": (
        "A separate satellite estimate (Google's Dynamic World model) of how likely a "
        "patch of ground is to be covered by trees specifically, versus NDVI's broader "
        "'is there vegetation of any kind' measure."
    ),
    "Heat-risk score": (
        "A combined score per ward: how much hotter it's gotten (LST change) minus how "
        "much greener it's gotten (NDVI change). Higher scores flag wards getting hotter "
        "without gaining canopy to offset it."
    ),
    "Correlation (r)": (
        "A number from -1 to 1 showing how strongly two things move together. Close to "
        "1 means they rise and fall in step; close to 0 means little to no relationship."
    ),
    "p-value": (
        "How likely it is that an observed pattern is just random chance. Under 0.05 is "
        "the usual line for 'probably a real pattern, not noise.'"
    ),
    "Ward": "GHMC's smallest administrative division — like a city council district. Hyderabad had 155 as of this project's data.",
    "GHMC": "Greater Hyderabad Municipal Corporation — the city government body responsible for the metro area covered here.",
    "Haritha Haram": (
        "Telangana state's official tree-planting program. This project checks "
        "satellite-observed canopy change against it."
    ),
}


def render_glossary() -> None:
    with st.expander("What do these terms mean?"):
        for term, definition in GLOSSARY.items():
            st.markdown(f"**{term}** — {definition}")


def render_scope_banner() -> None:
    st.warning(
        "Uses GHMC's pre-trifurcation 155-ward boundary (GHMC split into three separate "
        "corporations in Feb 2026 — not reflected here). 5 wards have no formal ward "
        "number in the source data and show blank heat-risk figures."
    )
    with st.expander("Which 5 wards, and why"):
        st.markdown(
            "Bandla Guda, Cantonment Area, Grampanchayat Peerzadi Guda, Kalavancha Gram "
            "Panchayath, and OU are annexed areas with no formal ward number in GHMC's "
            "GIS data, so the LST/heat-risk pipeline excluded them. They still appear on "
            "the map (grey, dashed) and in the leaderboard, with blank metric columns."
        )


def render_kpi_row(
    ndvi: pd.DataFrame, lst: pd.DataFrame, treecover: pd.DataFrame, heat_risk: pd.DataFrame
) -> None:
    col1, col2, col3, col4 = st.columns(4)

    ndvi_first, ndvi_last = ndvi["year"].min(), ndvi["year"].max()
    ndvi_delta = (
        ndvi.loc[ndvi["year"] == ndvi_last, "ndvi"].mean()
        - ndvi.loc[ndvi["year"] == ndvi_first, "ndvi"].mean()
    )
    col1.metric(
        "Citywide NDVI change", f"{ndvi_delta:+.3f}", help=f"{ndvi_first}–{ndvi_last}, city mean"
    )

    lst_first, lst_last = lst["year"].min(), lst["year"].max()
    lst_delta = (
        lst.loc[lst["year"] == lst_last, "lst_c"].mean()
        - lst.loc[lst["year"] == lst_first, "lst_c"].mean()
    )
    col2.metric(
        "Citywide LST change", f"{lst_delta:+.1f} °C", help=f"{lst_first}–{lst_last}, city mean"
    )

    tc_first, tc_last = treecover["year"].min(), treecover["year"].max()
    tc_delta = (
        treecover.loc[treecover["year"] == tc_last, "tree_prob"].mean()
        - treecover.loc[treecover["year"] == tc_first, "tree_prob"].mean()
    )
    col3.metric(
        "Tree-cover probability change",
        f"{tc_delta:+.3f}",
        help=f"Dynamic World, {tc_first}–{tc_last}",
    )

    n_flagged = int((heat_risk["heat_risk_score"] > heat_risk["heat_risk_score"].median()).sum())
    col4.metric("Wards above median heat-risk", f"{n_flagged} / {len(heat_risk)}")


def render_ward_selector(wards: pd.DataFrame) -> str:
    options = sorted(wards["ward_no"].unique(), key=lambda w: (len(w), w))
    labels = {row.ward_no: f"Ward {row.ward_no} — {row.ward_name}" for row in wards.itertuples()}
    return st.sidebar.selectbox(
        "Ward",
        options,
        format_func=lambda w: labels.get(w, w),
        key="selected_ward",
    )
