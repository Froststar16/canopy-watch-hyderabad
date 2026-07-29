"""
Ward choropleth built with leafmap/folium.

Manual binning instead of leafmap's add_data(scheme=...) — that path
routes through mapclassify, which doesn't tolerate NaN metric values
(some wards legitimately have none, see components.py's scope banner)
and throws a bare "zero-size array" error with no indication of why.
Wards with data get a quantile-colored layer; wards without get a
separate grey "no data" layer, so all 155 still render.
"""

from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd

import leafmap.foliumap as leafmap

METRIC_LABELS = {
    "heat_risk_score": "Heat-risk score",
    "ndvi_change": "NDVI change",
    "lst_change_c": "LST change (°C)",
    "tree_prob_change": "Tree-cover probability change",
}

HYDERABAD_CENTER = [17.385, 78.4867]
COLOR_SCALE = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]  # light -> dark
NO_DATA_COLOR = "#d9d9d9"


def _to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        return gdf.to_crs(4326)
    return gdf


def _color_for(value: float, breaks: list[float]) -> str:
    for edge, color in zip(breaks, COLOR_SCALE):
        if value <= edge:
            return color
    return COLOR_SCALE[-1]


def build_ward_choropleth(map_gdf: gpd.GeoDataFrame, metric: str) -> leafmap.Map:
    m = leafmap.Map(
        center=HYDERABAD_CENTER,
        zoom=10,
        draw_control=False,
        measure_control=False,
        toolbar_control=False,
    )

    has_data = _to_wgs84(map_gdf[map_gdf[metric].notna()].copy())
    missing = _to_wgs84(map_gdf[map_gdf[metric].isna()].copy())

    if has_data.empty:
        raise ValueError(
            f"No wards have a non-null value for '{metric}' — the ward_no join between "
            "the KML boundary and the metric CSVs likely isn't matching (e.g. the KML's "
            "'ward' field formatted differently than the CSVs' 'ward_no'). Compare "
            "data['wards']['ward_no'].head(10).tolist() against "
            "data['heat_risk']['ward_no'].head(10).tolist() to see the mismatch."
        )

    n_bins = min(5, has_data[metric].nunique())
    bins = pd.qcut(has_data[metric], q=n_bins, duplicates="drop")
    breaks = sorted(interval.right for interval in bins.cat.categories)

    def style_fn(feature):
        val = feature["properties"].get(metric)
        color = _color_for(val, breaks) if val is not None else NO_DATA_COLOR
        return {"fillColor": color, "color": "#666666", "weight": 0.5, "fillOpacity": 0.75}

    folium.GeoJson(
        has_data.to_json(),
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_no", "ward_name", metric],
            aliases=["Ward", "Name", METRIC_LABELS.get(metric, metric)],
        ),
        name="Wards",
    ).add_to(m)

    if not missing.empty:
        folium.GeoJson(
            missing.to_json(),
            style_function=lambda f: {
                "fillColor": NO_DATA_COLOR,
                "color": "#999999",
                "weight": 0.5,
                "fillOpacity": 0.4,
                "dashArray": "3,3",
            },
            tooltip=folium.GeoJsonTooltip(fields=["ward_no", "ward_name"], aliases=["Ward", "Name"]),
            name="No data",
        ).add_to(m)

    _add_legend(m, metric, breaks, has_missing=not missing.empty)
    return m


def _add_legend(m: leafmap.Map, metric: str, breaks: list[float], has_missing: bool) -> None:
    """Nice-to-have, wrapped defensively — a missing legend shouldn't take
    down a working map if leafmap's Map.get_root() ever changes shape."""
    try:
        rows = []
        lower = None
        for edge, color in zip(breaks, COLOR_SCALE):
            label = f"≤ {edge:.2f}" if lower is None else f"{lower:.2f} – {edge:.2f}"
            rows.append((color, label, "solid"))
            lower = edge
        if has_missing:
            rows.append((NO_DATA_COLOR, "No data", "dashed"))

        swatches = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">'
            f'<span style="width:14px;height:14px;background:{color};display:inline-block;'
            f'border:1px {style} #888;"></span>'
            f'<span style="font-size:12px;">{label}</span></div>'
            for color, label, style in rows
        )
        legend_html = f"""
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
                    background: white; padding: 8px 10px; border: 1px solid #999;
                    border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.3);">
          <div style="font-size:12px; font-weight:600; margin-bottom:4px;">
            {METRIC_LABELS.get(metric, metric)}
          </div>
          {swatches}
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
    except Exception:
        pass


if __name__ == "__main__":
    # quick standalone check: `python dashboard/map_view.py` from repo root
    # writes a test HTML you can open directly, no Streamlit required
    import data_loader  # noqa: E402  (only resolvable when run from dashboard/)

    data = data_loader.load_all()
    test_map = build_ward_choropleth(data["map_gdf"], "heat_risk_score")
    test_map.to_html("map_view_test.html")
    print("Wrote map_view_test.html — open it in a browser to sanity-check.")
