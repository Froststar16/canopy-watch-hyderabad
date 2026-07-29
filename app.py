"""Canopy Watch — Hyderabad dashboard. Run with: streamlit run app.py"""

import streamlit as st

from dashboard import charts, components, data_loader, map_view

st.set_page_config(page_title="Canopy Watch — Hyderabad", layout="wide")

st.title("Canopy Watch — Hyderabad")
st.caption(
    "Satellite-tracked tree canopy and land surface temperature change across "
    "GHMC, 2016–2025, checked against Telangana's Haritha Haram afforestation "
    "program."
)

data = data_loader.load_all()

components.render_glossary()
components.render_scope_banner()
components.render_kpi_row(data["ndvi"], data["lst"], data["treecover"], data["heat_risk"])

st.sidebar.header("Filters")
metric = st.sidebar.radio(
    "Map metric",
    options=list(map_view.METRIC_LABELS.keys()),
    format_func=lambda k: map_view.METRIC_LABELS[k],
)
selected_ward = components.render_ward_selector(data["wards"])

st.subheader("Ward map")
ward_map = map_view.build_ward_choropleth(data["map_gdf"], metric)
ward_map.to_streamlit(height=500)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Ward trends")
    fig_trend = charts.ward_trend_chart(data["ndvi"], data["lst"], data["treecover"], selected_ward)
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("NDVI vs LST correlation")
    ndvi_lst = data["ndvi"].merge(data["lst"], on=["ward_no", "year"])
    fig_corr = charts.correlation_scatter(
        ndvi_lst, "ndvi", "lst_c", "NDVI", "LST (°C)", "Citywide, all wards, all years"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

st.subheader("Heat-risk leaderboard")
leaderboard = data["heat_risk"][["ward_no", "ndvi_change", "lst_change_c", "heat_risk_score"]].merge(
    data["wards"][["ward_no", "ward_name"]], on="ward_no", how="right"
).sort_values("heat_risk_score", ascending=False)
st.dataframe(
    leaderboard[["ward_no", "ward_name", "ndvi_change", "lst_change_c", "heat_risk_score"]],
    use_container_width=True,
    height=350,
)
st.caption(
    f"{data['heat_risk']['ward_no'].nunique()} of {data['wards']['ward_no'].nunique()} wards "
    "have heat-risk data; blank rows are wards excluded from Phase 3's output — cause not "
    "yet identified."
)

st.subheader("Haritha Haram cross-check")
st.markdown(
    "The Telangana Forest Department's FMIS portal had no usable ward-level sapling data "
    "as of July 2026, so this is a satellite-only cross-check: Dynamic World tree-cover "
    "probability change against Phase 3's heat-risk score."
)
fig_cross = charts.correlation_scatter(
    data["cross_check"],
    "tree_prob_change",
    "heat_risk_score",
    "Tree-cover probability change",
    "Heat-risk score",
    "Tree-cover change vs heat risk",
)
st.plotly_chart(fig_cross, use_container_width=True)
st.info(
    "Tree-cover change correlates significantly with NDVI change (r=0.23, p=0.004, n=150) "
    "but not with the heat-risk score itself (r=0.09, p=0.27) — an open, unresolved finding, "
    "not a confirmed accountability story. *(See the glossary above for what r and p mean.)*"
)

col_a, col_b = st.columns(2)
with col_a:
    st.image(str(data_loader.OUTPUTS_DIR / "ndvi_vs_treecover_sanity_check.png"))
with col_b:
    st.image(str(data_loader.OUTPUTS_DIR / "haritha_haram_overlay.png"))

st.divider()
st.caption(
    "Methodology, data sources, and full write-up: "
    "[GitHub — canopy-watch-hyderabad](https://github.com/REPLACE_WITH_YOUR_USERNAME/canopy-watch-hyderabad)"
)
