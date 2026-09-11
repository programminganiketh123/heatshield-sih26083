"""India-centered heat-risk map rendering, using Folium (Leaflet.js) instead
of pydeck/deck.gl.

Why this replaces the old pydeck maps:
Deck.gl's WebGL-based MapView needs a real, hardware-accelerated WebGL2
context in the browser. On VMs, remote-desktop sessions, and machines with
GPU acceleration disabled, that context either fails to initialize or falls
back to a broken/garbled render -- which is what produced the oval "globe"
artifact instead of a flat India map.

Folium/Leaflet renders ordinary raster map tiles (plain images) plus
SVG/canvas markers. No WebGL involved anywhere, so it renders identically
on every machine, VM, or remote session -- at the cost of losing pydeck's
GPU-accelerated pan/zoom for very large point counts, which this app's
data sizes (dozens to low hundreds of points) never approach anyway.
"""
import folium
from streamlit_folium import st_folium

# Geographic center of India -- used as the default map center so the
# whole country is in view at a sensible default zoom.
INDIA_CENTER = (22.9734, 78.6569)


def render_heat_map(markers, center=INDIA_CENTER, zoom=5, height=420, key=None):
    """Render a Folium map with colored circle markers.

    markers: list of dicts, each with
        lat, lon (float)     -- required
        color (str, hex)     -- fill color for this point, required
        tooltip (str, html)  -- optional hover text
        radius (int, px)     -- optional marker size, default 7

    Returns the st_folium() result dict (includes click events, if any
    caller wants to react to a marker click -- most callers here don't
    need to, since a selectbox already provides reliable selection).
    """
    m = folium.Map(
        location=list(center),
        zoom_start=zoom,
        tiles="OpenStreetMap",  # no API key required, unlike Carto's tiles (as of 2026)
        control_scale=True,
    )

    for mk in markers:
        folium.CircleMarker(
            location=[mk["lat"], mk["lon"]],
            radius=mk.get("radius", 7),
            color="#f5faff",
            weight=1,
            fill=True,
            fill_color=mk.get("color", "#50c8ff"),
            fill_opacity=0.9,
            tooltip=folium.Tooltip(mk["tooltip"]) if mk.get("tooltip") else None,
        ).add_to(m)

    return st_folium(m, height=height, use_container_width=True, key=key)
