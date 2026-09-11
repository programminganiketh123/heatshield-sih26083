import html
import inspect
import re
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
IST=ZoneInfo("Asia/Kolkata")
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import requests
import streamlit as st

from src.thermal import heat_index_celsius, risk_category, wbgt_proxy
from src.risk_engine import calculate_risk
from src.india_locations import INDIA_LOCATIONS
from src.mapview import render_heat_map, INDIA_CENTER

# -----------------------------
# Location picker (whole-of-India) — same INDIA_LOCATIONS dataset that
# powers the India Map tab, flattened to a simple State -> City list so the
# header chip can be a real selector instead of a fixed "Hyderabad" label.
# -----------------------------
STATE_NAMES = sorted(INDIA_LOCATIONS.keys())
DEFAULT_LAT, DEFAULT_LON = 17.3850, 78.4867  # Hyderabad — used only as a last-resort fallback


def state_city_options(state_name):
    """Flatten a state's District -> [(city, lat, lon)] map into a sorted,
    de-duplicated {city_label: (lat, lon)} dict for the header picker."""
    cities = {}
    for city_list in INDIA_LOCATIONS.get(state_name, {}).items():
        for city_name, c_lat, c_lon in city_list[1]:
            cities.setdefault(city_name, (c_lat, c_lon))
    return dict(sorted(cities.items()))


if "loc_state" not in st.session_state:
    st.session_state["loc_state"] = "Telangana" if "Telangana" in STATE_NAMES else STATE_NAMES[0]
if "loc_city" not in st.session_state:
    st.session_state["loc_city"] = "Hyderabad"
if st.session_state["loc_city"] not in state_city_options(st.session_state["loc_state"]):
    _fallback_cities = state_city_options(st.session_state["loc_state"])
    st.session_state["loc_city"] = next(iter(_fallback_cities)) if _fallback_cities else "Hyderabad"

st.set_page_config(page_title=f"HEATSHIELD | {st.session_state['loc_city']}", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")

# -----------------------------
# Robust dashboard styling
# -----------------------------
st.markdown(
    """
<style>
:root{--bg:#030b15;--panel:#071625;--panel2:#0b1b2d;--line:#1d3652;--muted:#8ea4bd;--text:#eef6ff;--blue:#309dff;--cyan:#63d5ff;--orange:#ff9b3d;--red:#ff4f43;--green:#35d889;--yellow:#ffd13b;--purple:#9b74ff}
html,body,[class*="css"]{font-family:Inter,Segoe UI,Arial,sans-serif}
header, [data-testid="stHeader"]{height:0!important;min-height:0!important;visibility:hidden!important;display:none!important}
[data-testid="stToolbar"], #MainMenu, footer{display:none!important;visibility:hidden!important}
.stApp{background:radial-gradient(circle at 20% 0%,rgba(33,106,178,.15),transparent 26%),radial-gradient(circle at 95% 2%,rgba(255,82,58,.08),transparent 22%),var(--bg);color:var(--text)}
.block-container{max-width:none!important;padding:.35rem .55rem .5rem .55rem!important;margin:0!important}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#04101d,#020914);border-right:1px solid rgba(112,145,180,.25)!important;width:220px!important;min-width:220px!important;max-width:220px!important;flex:0 0 220px!important}
section[data-testid="stSidebar"]>div:first-child{width:220px!important}
section[data-testid="stSidebar"]>div{padding:.65rem .65rem 1rem!important}
[data-testid="stSidebar"] .stRadio label{font-size:13px!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.42rem!important}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:3px 2px 10px 3px;border-bottom:1px solid rgba(81,119,157,.18);margin-bottom:8px}
.brand{display:flex;align-items:center;gap:11px}.brand-fire{font-size:30px;line-height:1}.brand-title{font-size:28px;font-weight:900;letter-spacing:-.7px}.brand-sub{font-size:12px;color:var(--muted);margin-top:3px}.top-actions{display:flex;align-items:center;gap:12px}.live{padding:6px 10px;border-radius:999px;border:1px solid rgba(53,216,137,.45);background:rgba(53,216,137,.08);color:#70ef9e;font-size:10px;font-weight:900}.updated{font-size:9px;color:#8298b3}.loc{padding:8px 12px;border-radius:9px;border:1px solid rgba(110,149,190,.24);background:rgba(9,25,42,.84);font-size:10px;color:#eef5ff}
.panel{background:linear-gradient(145deg,rgba(7,22,38,.98),rgba(3,12,23,.98));border:1px solid rgba(98,136,175,.32);border-radius:13px;padding:10px;box-shadow:0 8px 24px rgba(0,0,0,.20);box-sizing:border-box}.head{display:flex;align-items:center;gap:8px;font-weight:850;font-size:15px;margin-bottom:8px}.num{width:27px;height:27px;border-radius:8px;background:linear-gradient(145deg,#ff5a36,#d63b2e);display:flex;align-items:center;justify-content:center;font-weight:900}.num.blue{background:linear-gradient(145deg,#6b83f0,#5a45bb)}.num.cyan{background:linear-gradient(145deg,#2f9fff,#176bd0)}.num.green{background:linear-gradient(145deg,#45d47e,#148650)}
.metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.metric{background:rgba(16,37,61,.86);border:1px solid rgba(108,148,195,.2);border-radius:9px;padding:8px;min-height:72px}.mlabel{font-size:8.5px;color:#94aac2}.mvalue{font-size:17px;font-weight:900;margin-top:5px}.mhint{font-size:8px;color:#53b7ff;margin-top:3px}
.risk{margin-top:8px;border:1px solid rgba(255,206,43,.62);border-radius:10px;background:linear-gradient(120deg,rgba(12,31,48,.98),rgba(5,16,28,.98));padding:10px}.riskgrid{display:grid;grid-template-columns:1.15fr .85fr;gap:10px;align-items:center}.eyebrow{font-size:9px;color:#ffd33b;font-weight:900}.score{font-size:36px;line-height:.9;font-weight:950;color:#ffc92e}.score-unit{font-size:15px;color:#8ea4bd}.rlabel{font-size:9px;color:#92a8c0}.rlevel{font-size:17px;font-weight:950;color:#ffd33b}.copy{font-size:9px;color:#b6c5d5;line-height:1.45;margin-top:7px}.tip{font-size:9px;color:#62d9ff;margin-top:6px}.gauge{height:62px;display:flex;align-items:flex-end;justify-content:center;position:relative}.arc{width:112px;height:56px;border-radius:120px 120px 0 0;border:9px solid var(--gauge-color,#38d98a);border-bottom:0;position:relative;filter:drop-shadow(0 0 6px rgba(255,208,51,.20))}.needle{position:absolute;width:3px;height:44px;background:white;bottom:-2px;left:58px;transform-origin:bottom center;transform:rotate(var(--gauge-deg,0deg));border-radius:2px;transition:transform .3s ease}
.section-title{font-size:10px;font-weight:900;margin:10px 0 4px}.forecast{width:100%;height:82px;background:#050e18;border:1px solid rgba(85,120,157,.18);border-radius:7px;overflow:hidden}.forecast svg{width:100%;height:100%}.forecast-meta{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:6px}.meta-box{padding:7px;border-radius:8px;background:rgba(15,35,58,.72);border:1px solid rgba(101,139,181,.16)}.meta-k{font-size:7px;color:#8198b3}.meta-v{font-size:12px;font-weight:900;margin-top:2px}
.selector-label{font-size:8px;color:#8fa5bf;margin-bottom:3px}.map-note{font-size:7.5px;color:#7f96b0;margin-top:5px}.map-legend{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}.legend{font-size:7.5px;color:#a4b6c8}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:3px}.hotspot{margin-top:7px;padding:8px;border:1px solid rgba(103,143,184,.18);border-radius:8px;background:rgba(18,38,62,.74)}.hot-top{display:flex;justify-content:space-between;align-items:center}.hot-name{font-size:10px;font-weight:900}.hot-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-top:5px}.hot-k{font-size:7px;color:#879db7}.hot-v{font-size:10px;font-weight:900;margin-top:2px}
.alert-main{padding:9px;border-radius:9px;background:linear-gradient(90deg,rgba(134,34,29,.50),rgba(66,22,25,.32));border:1px solid rgba(255,79,67,.64)}.alert-title{font-size:12px;font-weight:950}.alert-sub{font-size:8px;color:#d5a3a0;margin-top:3px}.alert-row{display:grid;grid-template-columns:25px 1fr auto;gap:7px;align-items:center;padding:7px 0;border-bottom:1px solid rgba(104,137,172,.13)}.alert-row:last-child{border-bottom:0}.aicon{font-size:17px}.aname{font-size:9px;font-weight:900}.acopy{font-size:7.5px;color:#8ca1ba;line-height:1.35;margin-top:2px}.priority{font-size:7px;font-weight:900;white-space:nowrap}.priority.red{color:#ff7166}.priority.gold{color:#ffc43a}.priority.blue{color:#67baff}.channels{font-size:7.5px;color:#879cb6;margin:5px 0}.action{margin-top:5px;padding:7px;border-radius:8px;border:1px solid rgba(83,135,183,.2);background:rgba(15,34,56,.78);text-align:center;font-size:9px;font-weight:900}
.explain{display:grid;grid-template-columns:1.25fr .75fr;gap:8px}.driver{margin:8px 0}.drow{display:flex;justify-content:space-between;font-size:8px}.drow span:last-child{color:#adc0d2}.bar{height:5px;border-radius:99px;background:#14273d;overflow:hidden;margin-top:4px}.fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#2f9fff,#ffd13b,#ff4e43)}.insight{padding:9px;border-radius:8px;border:1px solid rgba(60,214,133,.22);background:rgba(7,32,32,.48)}.it{font-size:10px;color:#67ea98;font-weight:900}.ic{font-size:8px;color:#b0c1d1;line-height:1.48;margin-top:5px}
.prec-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.prec{min-height:78px;padding:8px;border-radius:8px;background:rgba(17,36,59,.72);border:1px solid rgba(111,149,191,.15)}.pi{font-size:16px}.pt{font-size:8.5px;font-weight:900;margin-top:3px}.pc{font-size:7.4px;color:#8da3bc;line-height:1.32;margin-top:2px}
.water-grid{display:grid;grid-template-columns:.72fr 1.28fr .82fr;gap:7px}.water{padding:9px;border-radius:9px;border:1px solid rgba(55,143,238,.28);background:linear-gradient(145deg,rgba(7,39,70,.94),rgba(6,21,39,.98));min-height:124px}.ring{width:68px;height:68px;border-radius:50%;border:5px solid #2a93ff;display:flex;flex-direction:column;justify-content:center;align-items:center;margin:0 auto 7px}.rn{font-size:20px;font-weight:950;line-height:1}.ru{font-size:7px;color:#90a8c4}.glasses{font-size:16px;letter-spacing:1px}.wtotal{font-size:18px;font-weight:900;color:#66bcff}.small{font-size:7.5px;color:#8ca2bc}.day-card{padding:7px;border:1px solid rgba(103,143,185,.13);border-radius:8px;background:rgba(15,34,55,.62);text-align:center}.day{font-size:7.5px;color:#8ea6c0}.dscore{font-size:12px;font-weight:900;color:#ffd13b;margin-top:2px}.dtemp{font-size:8px;color:#e9f2fc;margin-top:1px}
.footer{padding:7px 2px;color:#66809b;font-size:8px}
.stButton>button{border-radius:8px;min-height:31px}.stTextInput input,.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input{border-radius:8px!important}.stSelectbox label,.stRadio label,.stSlider label,.stToggle label,.stCheckbox label{font-size:8.5px!important}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid rgba(110,145,180,.24);background:transparent}[data-testid="stTabs"] [data-baseweb="tab"]{background:rgba(16,37,61,.55);border:1px solid rgba(108,148,195,.22);border-bottom:none;border-radius:9px 9px 0 0;padding:9px 16px;font-weight:800;font-size:12px;color:#9db2c9}[data-testid="stTabs"] [data-baseweb="tab"]:hover{color:#eef6ff;background:rgba(16,37,61,.85)}[data-testid="stTabs"] [aria-selected="true"]{background:linear-gradient(145deg,rgba(47,159,255,.22),rgba(7,22,38,.98))!important;color:#eef6ff!important;border-color:rgba(53,157,255,.55)!important}[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background-color:#309dff!important;height:2.5px}[data-testid="stTabs"] [data-baseweb="tab-border"]{display:none}
@media(max-width:1150px){.metric-grid{grid-template-columns:repeat(2,1fr)}.riskgrid,.explain,.water-grid{grid-template-columns:1fr}.prec-grid{grid-template-columns:repeat(2,1fr)}.top-actions{gap:6px}.updated{display:none}}
</style>
""",
    unsafe_allow_html=True,
)

# Load sample hotspot data from the app folder. If the CSV is accidentally moved,
# keep the dashboard usable with a tiny built-in fallback instead of crashing.
hotspot_path = BASE_DIR / "data" / "sample_hotspots.csv"
if hotspot_path.exists():
    HOTSPOTS = pd.read_csv(hotspot_path)
else:
    HOTSPOTS = pd.DataFrame([
        ["Gachibowli",17.4401,78.3489,31,25.1,67,"MODERATE"],
        ["Madhapur",17.4483,78.3915,38,25.7,70,"MODERATE"],
        ["Kondapur",17.4580,78.3600,35,25.4,69,"MODERATE"],
        ["Kukatpally",17.4849,78.4138,42,25.8,72,"HIGH"],
        ["Secunderabad",17.4399,78.4983,46,26.1,74,"HIGH"],
        ["Begumpet",17.4447,78.4660,39,25.6,71,"MODERATE"],
        ["Charminar",17.3616,78.4747,51,26.4,77,"HIGH"],
        ["Mehdipatnam",17.3940,78.4399,44,26.0,74,"HIGH"],
        ["LB Nagar",17.3499,78.5570,56,26.8,80,"HIGH"],
        ["Uppal",17.4058,78.5591,48,26.2,75,"HIGH"],
        ["HITEC City",17.4483,78.3790,41,25.9,72,"HIGH"],
        ["Shamshabad",17.2403,78.4294,29,24.9,65,"MODERATE"],
    ], columns=["name","lat","lon","risk","temperature","humidity","category"])


RISK_COLORS = {
    "LOW": [53, 216, 137, 230],
    "MODERATE": [255, 209, 59, 235],
    "HIGH": [255, 155, 61, 238],
    "SEVERE": [255, 79, 67, 242],
    "EXTREME": [172, 80, 225, 245],
}

# Single source of truth for level -> hex color, reused by the badge chips
# and by the AI Risk Index gauge (previously the gauge had its own hardcoded
# green color + a fixed needle angle that never changed with the score).
LEVEL_COLORS = {
    "LOW": "#35d889", "MODERATE": "#ffd13b", "HIGH": "#ff9b3d",
    "SEVERE": "#ff5c52", "EXTREME": "#b05de7",
}


def badge(level):
    c = LEVEL_COLORS[level]
    return f'<span style="display:inline-block;padding:3px 6px;border-radius:5px;color:{c};background:{c}18;border:1px solid {c}55;font-size:7px;font-weight:900">{level}</span>'


def gauge_angle(score):
    """Map a 0-100 score to a -90..+90 degree needle rotation."""
    return -90 + (max(0.0, min(float(score), 100.0)) / 100.0) * 180.0


def validate_alert_destination(phone, channels):
    """Validate the demo destination required by SMS and WhatsApp channels."""
    normalized_phone = re.sub(r"[^\d+]", "", phone or "")
    phone_ok = bool(re.fullmatch(r"\+\d{10,15}", normalized_phone))
    phone_channels = {"SMS", "WhatsApp"} & set(channels)
    if phone_channels and not phone_ok:
        return False, "Enter a phone number with country code, e.g. +919876543210."
    if not channels:
        return False, "Select at least one alert channel."
    return True, f"Ready for simulated {', '.join(channels)} delivery."


def build_alert_message(city, state, score, level):
    """Create the short, judge-friendly alert shown in the live preview."""
    action = {
        "EXTREME": "Move vulnerable people to a cool place now and pause strenuous outdoor work.",
        "SEVERE": "Increase water breaks, activate shade/cooling support and review outdoor schedules.",
        "HIGH": "Hydrate, seek shade and check on elderly people, children and outdoor workers.",
    }.get(level, "Monitor conditions, hydrate regularly and keep cooling breaks available.")
    return (
        f"HEATSHIELD {level} ALERT | {city}, {state} | Risk {score:.0f}/100. "
        f"{action} This is a simulated demo notification."
    )


def append_alert_log(channels, destination, message, trigger):
    """Store a simulated delivery event in the current browser session only."""
    if "alert_log" not in st.session_state:
        st.session_state["alert_log"] = []
    timestamp = datetime.now(IST).strftime("%d %b %Y, %I:%M:%S %p")
    for channel in channels:
        st.session_state["alert_log"].insert(0, {
            "time": timestamp,
            "channel": channel,
            "destination": destination,
            "status": "SIMULATED",
            "trigger": trigger,
            "message": message,
        })
    st.session_state["alert_log"] = st.session_state["alert_log"][:30]


def svg_forecast(times, temps, feels, threshold):
    w, h = 700, 120
    left, right, top, bottom = 30, 14, 8, 30
    vals = np.array(list(temps) + list(feels) + [threshold], dtype=float)
    ymin, ymax = float(vals.min() - 1), float(vals.max() + 2)
    def xy(i, v):
        x = left + (w-left-right) * i / max(1, len(temps)-1)
        y = h-bottom - (h-top-bottom) * (v-ymin) / max(1e-6, ymax-ymin)
        return x,y
    p1 = " ".join(f"{xy(i,temps[i])[0]:.1f},{xy(i,temps[i])[1]:.1f}" for i in range(len(temps)))
    p2 = " ".join(f"{xy(i,feels[i])[0]:.1f},{xy(i,feels[i])[1]:.1f}" for i in range(len(feels)))
    th_y = xy(0, threshold)[1]
    peak_i = int(np.argmax(feels))
    px, py = xy(peak_i, feels[peak_i])
    labels = [(0,times[0]), (len(times)//3,times[len(times)//3]), (len(times)*2//3,times[len(times)*2//3]), (len(times)-1,times[-1])]
    label_svg = "".join(f'<text x="{xy(i, ymin)[0]:.1f}" y="112" fill="#8da2ba" font-size="8" text-anchor="middle">{html.escape(str(t))}</text>' for i,t in labels)
    return f'''<div class="forecast"><svg viewBox="0 0 {w} {h}" preserveAspectRatio="none">
      <line x1="30" x2="686" y1="{xy(0,round((ymin+ymax)/2,1))[1]:.1f}" y2="{xy(0,round((ymin+ymax)/2,1))[1]:.1f}" stroke="#1c3045"/>
      <line x1="30" x2="686" y1="{th_y:.1f}" y2="{th_y:.1f}" stroke="#ff4f43" stroke-dasharray="5 4" opacity=".9"/>
      <polyline points="{p1}" fill="none" stroke="#1e8eff" stroke-width="2.8"/>
      <polyline points="{p2}" fill="none" stroke="#71cdfc" stroke-width="2.2" stroke-dasharray="5 4"/>
      <circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#ff4f43" stroke="#fff" stroke-width="1.2"/>
      <text x="{min(px+8,620):.1f}" y="{max(py-7,14):.1f}" fill="#ff756c" font-size="8" font-weight="700">Peak</text>
      {label_svg}
    </svg></div>'''


def weather_label(code):
    return {0:"Clear",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",51:"Drizzle",53:"Drizzle",61:"Rain",63:"Rain",65:"Heavy rain",80:"Showers",95:"Thunderstorm"}.get(int(code), "Current")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_weather(lat, lon):
    # lat/lon are real cache-key arguments (not a closure over a global) so
    # switching the header location picker actually fetches a fresh city
    # instead of silently reusing a cached Hyderabad reading.
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code,shortwave_radiation",
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,shortwave_radiation,precipitation_probability",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 5, "timezone": "Asia/Kolkata",
        }, timeout=12,
    )
    r.raise_for_status()
    return r.json(), None


def get_weather(lat, lon):
    try:
        return fetch_weather(lat, lon)
    except Exception as exc:
        return None, str(exc)


@st.cache_data(ttl=180, show_spinner=False)
def fetch_city_weather(lat, lon):
    """Live current weather for an arbitrary lat/lon (used by the India Map page)."""
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code,shortwave_radiation",
            "timezone": "Asia/Kolkata",
        }, timeout=12,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_india_overview(points):
    """Batched current-weather fetch for a fixed tuple of (lat, lon) points --
    one Open-Meteo request for the whole set instead of one call per location."""
    lats = ",".join(f"{p[0]:.4f}" for p in points)
    lons = ",".join(f"{p[1]:.4f}" for p in points)
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lats, "longitude": lons,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation",
            "timezone": "Asia/Kolkata",
        }, timeout=25,
    )
    r.raise_for_status()
    payload = r.json()
    return payload if isinstance(payload, list) else [payload]


# -----------------------------
# Sidebar controls
# -----------------------------
if "demo_controls_enabled" not in st.session_state:
    st.session_state["demo_controls_enabled"] = False

with st.sidebar:
    st.markdown('<div style="text-align:center;padding-top:2px"><div style="font-size:48px;line-height:1">🛡️</div><div style="font-size:19px;font-weight:900">HEATSHIELD</div><div style="color:#ff5936;font-size:10px;font-weight:900">SIH26083</div></div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:0;border-top:1px solid rgba(110,145,180,.24);margin:18px 0">', unsafe_allow_html=True)
    st.markdown("**Navigation**")
    page = st.radio("Navigation", ["Dashboard","Analytics","History","Reports","India Map","Settings","About"], index=0, label_visibility="collapsed")
    st.markdown('<hr style="border:0;border-top:1px solid rgba(110,145,180,.24);margin:10px 0 12px">', unsafe_allow_html=True)
    st.markdown("**System Status**")
    st.success("● All systems operational")
    if st.session_state["demo_controls_enabled"]:
        st.markdown("**Demo Controls**")
        st.caption("Raise temperature to demonstrate how thermal stress and alerts escalate.")
        sim_temperature = st.slider("Temperature °C", 20.0, 50.0, 39.5, 0.5)
        sim_humidity = st.slider("Humidity %", 30, 95, 68)
        sim_radiation = st.slider("Solar radiation W/m²", 0, 1000, 850, 25)
        sim_wind = st.slider("Wind km/h", 0, 20, 6)
        st.caption("Demo simulator: change temperature, humidity, radiation or wind to demonstrate the prototype risk. The live score remains visible for comparison.")
    else:
        sim_temperature, sim_humidity, sim_radiation, sim_wind = None, None, None, None
        st.caption("Demo simulator is off. Turn it on anytime from Settings → Demo Controls.")

# -----------------------------
# Header: brand + whole-of-India location picker + refresh
# -----------------------------
# Rendered (and resolved) before the weather fetch, since the selected
# State/City below determines which coordinates get fetched.
updated = datetime.now(IST).strftime("%I:%M %p • %d %b %Y") + "IST"
top_l, top_state, top_city, top_r = st.columns([3.6, 1.25, 1.45, 0.9])
with top_l:
    # weather_error isn't known yet at this point in the script (the fetch
    # happens further down, since it needs LAT/LON resolved from the
    # selectors below first) -- so render into a placeholder now and fill
    # it in for real once we know whether we're live or on fallback.
    topbar_slot = st.empty()
    topbar_slot.markdown(f'''<div class="topbar"><div class="brand"><div class="brand-fire">🔥</div><div><div class="brand-title">HEATSHIELD</div><div class="brand-sub">{html.escape(st.session_state["loc_city"])} Heat Intelligence Platform</div></div></div><div class="top-actions"><span class="live">● LIVE</span><span class="updated">Last updated: {updated} ↻</span></div></div>''', unsafe_allow_html=True)
with top_state:
    st.markdown('<div class="selector-label">⌖ State / UT</div>', unsafe_allow_html=True)
    st.selectbox("State / UT", STATE_NAMES, key="loc_state", label_visibility="collapsed")
with top_city:
    _city_options = list(state_city_options(st.session_state["loc_state"]).keys())
    if st.session_state["loc_city"] not in _city_options and _city_options:
        st.session_state["loc_city"] = _city_options[0]
    st.markdown('<div class="selector-label">City / Town</div>', unsafe_allow_html=True)
    st.selectbox("City / Town", _city_options, key="loc_city", label_visibility="collapsed")
with top_r:
    st.markdown('<div class="selector-label">&nbsp;</div>', unsafe_allow_html=True)
    if st.button("↻ Refresh", width="stretch", help="Refresh live weather now"):
        fetch_weather.clear()
        st.rerun()

LOC_STATE = st.session_state["loc_state"]
LOC_CITY = st.session_state["loc_city"]
LAT, LON = state_city_options(LOC_STATE).get(LOC_CITY, (DEFAULT_LAT, DEFAULT_LON))
IS_HYDERABAD = LOC_CITY == "Hyderabad" and LOC_STATE == "Telangana"

weather, weather_error = get_weather(LAT, LON)
if weather_error is not None:
    topbar_slot.markdown(f'''<div class="topbar"><div class="brand"><div class="brand-fire">🔥</div><div><div class="brand-title">HEATSHIELD</div><div class="brand-sub">{html.escape(LOC_CITY)} Heat Intelligence Platform</div></div></div><div class="top-actions"><span class="live" style="background:#5b6472">● DEMO FALLBACK</span><span class="updated">Last updated: {updated} ↻</span></div></div>''', unsafe_allow_html=True)
if weather is None:
    now = datetime.now(IST)
    current = {"temperature_2m": 39.5,"relative_humidity_2m": 68.0,"apparent_temperature":42.0,"wind_speed_10m":6.0,"weather_code":1,"shortwave_radiation":850.0}
    hourly = {"time": [f"{now.date()} {h:02d}:00" for h in range(24)], "temperature_2m": [39,39,38,38,37,37,37,38,39,40,41,42,42,41,40,39,38,37,36,36,35,35,35,34], "relative_humidity_2m":[68]*24,"apparent_temperature":[40,40,39,39,38,39,40,41,42,43,44,45,45,44,43,42,40,39,38,37,36,36,35,35],"wind_speed_10m":[6]*24,"shortwave_radiation":[0,0,0,0,0,0,30,150,350,600,800,850,900,850,700,500,250,80,0,0,0,0,0,0]}
    daily = {
        "time": [str((now + timedelta(days=i)).date()) for i in range(5)],
        "temperature_2m_max": [42, 43.5, 44, 41, 39.5],
        "temperature_2m_min": [34, 35, 35.5, 33, 32],
        "precipitation_probability_max": [15, 10, 5, 20, 25],
    }
    data = {"current":current,"hourly":hourly,"daily":daily}
else:
    data = weather

current = data["current"]
hourly = data["hourly"]
daily = data.get("daily", {})

temp = float(current["temperature_2m"])
rh = float(current["relative_humidity_2m"])
feels = float(current["apparent_temperature"])
wind = float(current["wind_speed_10m"])
# Use the actual current-hour reading from Open-Meteo's "current" block
# instead of blindly taking the first hourly value (which is usually
# midnight / ~0 W/m² and was previously masking a stale reading).
rad_now = float(current.get("shortwave_radiation") or 0.0)

# When the Demo Controls toggle (Settings) is off, sim_* were left as None in
# the sidebar -- fall back to the real live readings so the whole dashboard
# runs on live data only, with no separate "demo scenario" delta.
if sim_humidity is None:
    sim_temperature = temp
    sim_humidity = rh
if sim_radiation is None:
    sim_radiation = rad_now
if sim_wind is None:
    sim_wind = wind

baseline = calculate_risk(temp, rh, wind, max(rad_now, 250), 16000, 18, 32, 72)
sim = calculate_risk(sim_temperature, sim_humidity, sim_wind, sim_radiation, 16000, 18, 32, 72)
score = float(baseline["overall_risk"])
level = baseline["risk_category"]
demo_delta = float(sim["overall_risk"]) - float(baseline["overall_risk"])
scenario_score = float(sim["overall_risk"]) if st.session_state["demo_controls_enabled"] else score
scenario_level = sim["risk_category"] if st.session_state["demo_controls_enabled"] else level
delta_color = "#72e7a1" if demo_delta <= 0 else "#ffb45b"
hi = heat_index_celsius(temp, rh)
wbgt = wbgt_proxy(temp, rh, wind, max(rad_now, 250))

if weather_error:
    st.warning(f"Live weather for {LOC_CITY} is temporarily unavailable. Showing a cached/demo-safe fallback for the dashboard.")

if page != "Dashboard":
    st.markdown(f'<div class="panel"><div class="head"><div class="num">{page[0]}</div><div>{page}</div></div>', unsafe_allow_html=True)
    if page == "Analytics":
        st.write("### 5-day outlook")
        if daily.get("time"):
            cards = st.columns(min(5, len(daily["time"])))
            for i, c in enumerate(cards):
                day = pd.to_datetime(daily["time"][i]).strftime("%a %d")
                c.metric(day, f"{daily['temperature_2m_max'][i]:.0f}°C", f"min {daily['temperature_2m_min'][i]:.0f}°C")
        st.write("### Risk drivers")
        st.write(f"Current prototype screening score: **{score:.0f}/100 ({level})**. Demo scenario: **{scenario_score:.0f}/100 ({scenario_level})**, temperature **{sim_temperature:.1f}°C**, humidity **{sim_humidity}%**, radiation **{sim_radiation} W/m²**, wind **{sim_wind} km/h**.")
    elif page == "History":
        hist = pd.DataFrame({"Day":["-4d","-3d","-2d","-1d","Today"],"Risk":[58,61,56,64,round(score)],"Category":[risk_category(x) for x in [58,61,56,64,score]]})
        st.dataframe(hist, width="stretch", hide_index=True)
    elif page == "Reports":
        st.write("### Action-ready report")
        st.write(f"{LOC_CITY}, {LOC_STATE} • Risk {score:.0f}/100 • {level}\n\nPeak risk should be reviewed against the forecast window. Recommended actions include hydration, shade, work-hour changes and preparedness for vulnerable groups.")
        st.download_button("Export report summary", f"HEATSHIELD {LOC_CITY}\nRisk: {score:.0f}/100\nLevel: {level}\n", file_name="heatshield_report.txt")
    elif page == "India Map":
        st.write("### Real-time Heat Map — India")
        st.caption("National overview uses one live-fetched representative location per state/UT (a single batched request). Drill into State → District → City below for a specific location.")

        state_names = STATE_NAMES
        rep_points = []
        for st_name in state_names:
            first_district = next(iter(INDIA_LOCATIONS[st_name]))
            city_name, c_lat, c_lon = INDIA_LOCATIONS[st_name][first_district][0]
            rep_points.append({"state": st_name, "district": first_district, "city": city_name, "lat": c_lat, "lon": c_lon})

        overview_error = None
        try:
            raw = fetch_india_overview(tuple((p["lat"], p["lon"]) for p in rep_points))
        except Exception as exc:
            raw, overview_error = [], str(exc)

        rows = []
        for p, w in zip(rep_points, raw or []):
            cur = (w or {}).get("current", {})
            t = cur.get("temperature_2m")
            h = cur.get("relative_humidity_2m")
            if t is None or h is None:
                continue
            wd = float(cur.get("wind_speed_10m") or 0.0)
            rad = float(cur.get("shortwave_radiation") or 0.0)
            risk = calculate_risk(float(t), float(h), wd, max(rad, 250), 12000, 16, 30, 65)
            rows.append({
                "state": p["state"], "district": p["district"], "city": p["city"],
                "lat": p["lat"], "lon": p["lon"], "temperature": float(t), "humidity": float(h),
                "wind": wd, "risk": risk["overall_risk"], "level": risk["risk_category"],
            })
        nat_df = pd.DataFrame(rows)

        if overview_error:
            st.warning("Live nationwide weather is temporarily unavailable -- showing whatever data loaded.")

        st.markdown("#### Filter National Overview")
        f1, f2, f3 = st.columns([1.6, 1, 1])
        with f1:
            india_level_filter = st.multiselect(
                "Risk level",
                ["LOW", "MODERATE", "HIGH", "SEVERE", "EXTREME"],
                default=["LOW", "MODERATE", "HIGH", "SEVERE", "EXTREME"],
                key="india_level_filter",
                help="Show only states/UTs currently at these heat-risk levels.",
            )
        with f2:
            india_min_temp = st.slider("Min temp (°C)", 10, 48, 10, key="india_min_temp")
        with f3:
            india_search = st.text_input("Search state/city", value="", placeholder="e.g. Kerala", key="india_search")

        if nat_df.empty:
            nat_df_view = nat_df
        else:
            nat_df_view = nat_df[nat_df["level"].isin(india_level_filter) & (nat_df["temperature"] >= india_min_temp)]
            if india_search.strip():
                q = india_search.strip().lower()
                nat_df_view = nat_df_view[
                    nat_df_view["state"].str.lower().str.contains(q)
                    | nat_df_view["city"].str.lower().str.contains(q)
                ]
        st.caption(f"Showing {len(nat_df_view)} of {len(nat_df)} states/UTs after filters.")

        st.markdown("#### Drill down: State → District → City")
        st.caption(f"Defaults to your header selection ({LOC_CITY}, {LOC_STATE}) — change it here to explore any other Indian district.")
        d1, d2, d3 = st.columns(3)
        with d1:
            _default_state_idx = state_names.index(LOC_STATE) if LOC_STATE in state_names else 0
            sel_state = st.selectbox("State / UT", state_names, index=_default_state_idx, key="india_state_select")
        districts = sorted(INDIA_LOCATIONS[sel_state].keys())
        with d2:
            sel_district = st.selectbox("District", districts, key="india_district_select")
        cities = INDIA_LOCATIONS[sel_state][sel_district]
        city_labels = [c[0] for c in cities]
        with d3:
            sel_city_label = st.selectbox("City / Town", city_labels, key="india_city_select")
        sel_city = next(c for c in cities if c[0] == sel_city_label)
        city_lat, city_lon = sel_city[1], sel_city[2]

        city_weather, city_err = None, None
        try:
            city_weather = fetch_city_weather(city_lat, city_lon)
        except Exception as exc:
            city_err = str(exc)

        table_view_india = st.toggle(
            "Table view", value=False, key="india_table_toggle",
            help="Switch to a plain data table instead of the map.",
        )

        markers = []
        if not nat_df_view.empty:
            for _, r in nat_df_view.iterrows():
                markers.append({
                    "lat": r["lat"], "lon": r["lon"],
                    "color": LEVEL_COLORS.get(r["level"], "#50c8ff"),
                    "radius": 6,
                    "tooltip": (
                        f"<b>{html.escape(str(r['state']))}</b><br/>"
                        f"{html.escape(str(r['city']))} ({html.escape(str(r['district']))})<br/>"
                        f"Risk: {r['risk']:.0f}/100 ({r['level']})<br/>"
                        f"Temp: {r['temperature']:.1f}°C · Humidity: {r['humidity']:.0f}%"
                    ),
                })
        markers.append({
            "lat": city_lat, "lon": city_lon, "color": "#50c8ff", "radius": 9,
            "tooltip": f"<b>{html.escape(sel_city_label)}</b> (selected)",
        })

        if table_view_india or nat_df_view.empty:
            if not nat_df_view.empty:
                st.dataframe(
                    nat_df_view[["state", "district", "city", "temperature", "humidity", "risk", "level"]].round(1),
                    width="stretch", hide_index=True,
                )
            elif nat_df.empty:
                st.info("No nationwide data loaded yet.")
            else:
                st.info("No states/UTs match the current filters. Try widening the risk level or lowering the min temperature.")
        else:
            render_heat_map(markers, center=INDIA_CENTER, zoom=4.4, height=420, key="india-national-map")

        st.markdown(
            '<div class="map-legend">'
            '<span class="legend"><span class="dot" style="background:#35d889"></span>Low</span>'
            '<span class="legend"><span class="dot" style="background:#ffd13b"></span>Moderate</span>'
            '<span class="legend"><span class="dot" style="background:#ff9b3d"></span>High</span>'
            '<span class="legend"><span class="dot" style="background:#ff4f43"></span>Severe</span>'
            '<span class="legend"><span class="dot" style="background:#b05de7"></span>Extreme</span>'
            '</div>', unsafe_allow_html=True,
        )

        st.markdown("#### Selected location")
        if city_err or not city_weather:
            st.warning("Could not fetch live weather for this location right now.")
        else:
            cw = city_weather.get("current", {})
            ct = float(cw.get("temperature_2m", 0.0))
            ch = float(cw.get("relative_humidity_2m", 0.0))
            cf = float(cw.get("apparent_temperature", ct))
            cwd = float(cw.get("wind_speed_10m", 0.0))
            crad = float(cw.get("shortwave_radiation") or 0.0)
            crisk = calculate_risk(ct, ch, cwd, max(crad, 250), 12000, 16, 30, 65)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Temperature", f"{ct:.1f}°C")
            m2.metric("Feels Like", f"{cf:.1f}°C")
            m3.metric("Humidity", f"{ch:.0f}%")
            m4.metric("Heat Risk", f"{crisk['overall_risk']:.0f}/100", crisk["risk_category"])
            st.caption(f"{sel_city_label}, {sel_district}, {sel_state} • Live via Open-Meteo")

        st.caption("Sample district coverage for this prototype -- extend src/india_locations.py to add every district for full national coverage.")
    elif page == "Settings":
        st.checkbox("Auto refresh every 60 seconds", value=True)
        st.checkbox("Use fallback if live feed fails", value=True)
        st.selectbox("Risk model", ["Prototype HTSS normalized score", "Validated ML model (future)"])

        st.markdown("---")
        st.markdown("**Demo Controls**")
        demo_on = st.toggle(
            "Show demo simulator sliders in the sidebar",
            value=st.session_state["demo_controls_enabled"],
            help="When on, the sidebar shows humidity/solar-radiation/wind sliders to simulate a scenario for presentations. When off, the dashboard runs on live weather only.",
        )
        st.session_state["demo_controls_enabled"] = demo_on
        st.caption("Off by default for a clean, real-data-only dashboard. Switch on for live demo presentations.")

        st.markdown("---")
        st.markdown("**Notification Preferences — SMS / WhatsApp / Email Alerts**")
        st.caption("Add a phone number and/or email to receive heat-risk alerts. Prototype only: details are kept for this session and no message is actually sent yet.")
        pref_phone = st.text_input("Phone number (with country code)", value=st.session_state.get("alert_phone", ""), placeholder="+91 9XXXXXXXXX", key="settings_phone_input")
        pref_email = st.text_input("Email address", value=st.session_state.get("alert_email", ""), placeholder="you@example.com", key="settings_email_input")
        pref_channels = st.multiselect(
            "Alert channels",
            ["SMS", "WhatsApp", "Email", "Push"],
            default=st.session_state.get("alert_channels", ["SMS", "WhatsApp"]),
            key="settings_channels_input",
        )
        if st.button("Save Notification Preferences", width="stretch"):
            st.session_state["alert_phone"] = pref_phone
            st.session_state["alert_email"] = pref_email
            st.session_state["alert_channels"] = pref_channels
            if pref_phone or pref_email:
                st.success(f"Saved. Alert Centre will show you as subscribed via {', '.join(pref_channels) if pref_channels else 'no channel'}.")
            else:
                st.warning("Add a phone number or email before saving.")
    else:
        st.markdown(f"**HEATSHIELD SIH26083** — Impact-based heat-health early warning, piloted for Hyderabad and selectable for any Indian state/city (currently viewing **{LOC_CITY}, {LOC_STATE}**).")
        st.write("Forecast → Thermal Stress → Vulnerability → AI Risk → Hyperlocal GIS → Actionable Warning")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Main command center -- one tab per section, so selecting a tab shows only
# that section instead of a dense multi-column grid. Tab labels mirror the
# numbered panels (1-6) that were shown before.
dash_tabs = st.tabs([
    "1 · Temperature & Risk",
    "2 · Live Map",
    "3 · Alert Centre",
    "4 · Why the Risk?",
    "5 · Precautions",
    "6 · Water Reminder",
])

with dash_tabs[0]:
    st.markdown('<div class="panel"><div class="head"><div class="num">1</div><div>Temperature &amp; Heat Risk</div></div>', unsafe_allow_html=True)
    _display_temp = sim_temperature if st.session_state["demo_controls_enabled"] else temp
    _temp_hint = "Demo scenario" if st.session_state["demo_controls_enabled"] else "Live"
    st.markdown(f'''<div class="metric-grid">
      <div class="metric"><div class="mlabel">🌡 Temperature</div><div class="mvalue">{_display_temp:.1f}°C</div><div class="mhint">{_temp_hint}</div></div>
      <div class="metric"><div class="mlabel">💧 Humidity</div><div class="mvalue">{sim_humidity:.0f}%</div><div class="mhint">Heat load</div></div>
      <div class="metric"><div class="mlabel">🌬 Wind Speed</div><div class="mvalue">{sim_wind:.1f} km/h</div><div class="mhint">Cooling</div></div>
      <div class="metric"><div class="mlabel">🌤 Feels Like</div><div class="mvalue">{feels:.1f}°C</div><div class="mhint">{weather_label(current['weather_code'])}</div></div>
    </div>''', unsafe_allow_html=True)
    _gauge_color = LEVEL_COLORS.get(level, "#38d98a")
    _gauge_deg = gauge_angle(score)
    _demo_note = ""
    if abs(demo_delta) >= 1:
        _sign = "+" if demo_delta >= 0 else ""
        _demo_note = f'<div class="tip" style="color:{delta_color}">▲ Demo scenario (sidebar sliders): {sim["overall_risk"]:.0f}/100 ({_sign}{demo_delta:.0f} vs live)</div>'
    st.markdown(f'''<div class="risk"><div class="riskgrid"><div><div class="eyebrow">AI HEAT RISK INDEX</div><div style="margin-top:6px"><span class="score">{score:.0f}</span> <span class="score-unit">/ 100</span></div></div><div><div class="rlabel">Risk Level</div><div class="rlevel">{level}</div><div class="gauge"><div class="arc" style="--gauge-color:{_gauge_color}"><div class="needle" style="--gauge-deg:{_gauge_deg:.1f}deg"></div></div></div></div></div><div class="copy">AI assesses current environmental heat-stress potential. Main drivers: humidity, temperature, wind cooling and solar load.</div><div class="tip">✦ Stay hydrated, use shade and schedule cooling breaks.</div>{_demo_note}</div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Next 24 Hours Forecast</div>', unsafe_allow_html=True)
    tvals = [float(x) for x in hourly.get("temperature_2m",[])[:24]]
    fvals = [float(x) for x in hourly.get("apparent_temperature",[])[:24]]
    if tvals and fvals:
        ts = pd.to_datetime(hourly["time"][:24]).strftime("%a %H:%M").tolist()
        st.markdown(svg_forecast(ts, tvals, fvals, 40), unsafe_allow_html=True)
    if tvals and fvals:
        peak_i = int(np.argmax(fvals))
        st.markdown(f'''<div class="forecast-meta"><div class="meta-box"><div class="meta-k">Peak Heat Stress Time</div><div class="meta-v">{ts[peak_i]}</div></div><div class="meta-box"><div class="meta-k">Forecast Max</div><div class="meta-v">{max(tvals):.1f}°C</div></div></div>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with dash_tabs[1]:
    st.markdown(f'<div class="panel"><div class="head"><div class="num blue">2</div><div>{html.escape(LOC_CITY)} Real-time Map</div></div>', unsafe_allow_html=True)

    if not IS_HYDERABAD:
        # Neighbourhood-level hotspot data only exists for the Hyderabad pilot
        # (data/sample_hotspots.csv). For any other selected city, show a live
        # single-point city view instead of fabricating ward-level numbers.
        st.caption(f"Neighbourhood-level hotspots are currently available for the Hyderabad pilot only. Showing a live city-level reading for {LOC_CITY}, {LOC_STATE}.")
        _city_risk = calculate_risk(temp, rh, wind, max(rad_now, 250), 16000, 18, 32, 72)
        cm1, cm2, cm3, cm4 = st.columns(4)
        cm1.metric("Temperature", f"{temp:.1f}°C")
        cm2.metric("Feels Like", f"{feels:.1f}°C")
        cm3.metric("Humidity", f"{rh:.0f}%")
        cm4.metric("Heat Risk", f"{_city_risk['overall_risk']:.0f}/100", _city_risk["risk_category"])

        _single_df = pd.DataFrame([{
            "name": LOC_CITY, "lat": LAT, "lon": LON,
            "risk": _city_risk["overall_risk"], "level": _city_risk["risk_category"],
            "temperature": round(temp, 1), "humidity": round(rh, 0),
        }])
        single_table_view = st.toggle(
            "Table view", value=False, key="single_city_table_toggle",
            help="Switch to a plain data table instead of the map.",
        )
        if single_table_view:
            st.dataframe(_single_df[["name", "temperature", "humidity", "risk", "level"]], width="stretch", hide_index=True)
        else:
            render_heat_map(
                [{
                    "lat": LAT, "lon": LON, "radius": 9,
                    "color": LEVEL_COLORS.get(_city_risk["risk_category"], "#50c8ff"),
                    "tooltip": (
                        f"<b>{html.escape(LOC_CITY)}</b><br/>"
                        f"Risk: {_city_risk['overall_risk']:.0f}/100 ({_city_risk['risk_category']})<br/>"
                        f"Temp: {temp:.1f}°C · Humidity: {rh:.0f}%"
                    ),
                }],
                center=(LAT, LON), zoom=10.5, height=320, key="single-city-map",
            )
        st.markdown(
            f'<div class="map-note">Add a validated ward/neighbourhood dataset for {html.escape(LOC_CITY)} to '
            'data/ to unlock hyperlocal hotspots here, the same way the Hyderabad pilot does today.</div></div>',
            unsafe_allow_html=True,
        )

    if IS_HYDERABAD:
        forecast_window = st.radio("Forecast window", ["Today","Tomorrow","+2 Days","+3 Days","+4 Days"], index=0, horizontal=True, label_visibility="collapsed")
        day_shift = {"Today":0,"Tomorrow":1,"+2 Days":2,"+3 Days":3,"+4 Days":4}[forecast_window]
        # Hotspot risk now runs through the same calculate_risk() engine as the
        # headline AI Heat Risk Index, instead of an arbitrary "+2 points per
        # forecast day" offset on a static CSV number. Each hotspot's prototype
        # temperature is anchored to today's live citywide temperature, and the
        # forecast-day shift uses Open-Meteo's real daily max-temperature trend.
        frame = HOTSPOTS.copy()
        daily_max = daily.get("temperature_2m_max", [])
        if len(daily_max) > day_shift:
            # Normal case: the requested forecast day is available.
            day_temp_delta = float(daily_max[day_shift] - daily_max[0])
        elif len(daily_max) >= 2:
            # Fewer days than requested came back (e.g. a truncated API
            # response) — use the furthest day we actually have instead of
            # silently collapsing every later toggle to zero.
            day_temp_delta = float(daily_max[-1] - daily_max[0])
        else:
            day_temp_delta = 0.0
        city_temp_baseline = float(HOTSPOTS["temperature"].mean())

        def _hotspot_adj_temp(row):
            return row["temperature"] + (temp - city_temp_baseline) + day_temp_delta

        # Store the forecast-day-adjusted temperature as its own column
        # instead of only using it transiently inside the risk calc — every
        # display (map tooltip, table, hotspot detail card) needs to read
        # *this* value, not the raw CSV "temperature", or the readout looks
        # frozen when the forecast window is changed.
        frame["temp_view"] = frame.apply(_hotspot_adj_temp, axis=1)

        def _hotspot_risk(row):
            result = calculate_risk(row["temp_view"], row["humidity"], wind, max(rad_now, 250), 16000, 18, 32, 72)
            return result["overall_risk"]

        frame["risk_view"] = frame.apply(_hotspot_risk, axis=1).clip(0, 100)
        frame["level_view"] = frame["risk_view"].apply(risk_category)

        # Optional filter so the map / list can be narrowed to just the risk
        # levels the user cares about (e.g. only HIGH and above).
        all_levels = ["LOW", "MODERATE", "HIGH", "SEVERE", "EXTREME"]
        level_filter = st.multiselect(
            "Filter hotspots by risk level",
            all_levels,
            default=all_levels,
            key="hyd_level_filter",
            help="Show only hotspots at these risk levels on the map and in the list below.",
        )
        frame_filtered = frame[frame["level_view"].isin(level_filter)] if level_filter else frame.iloc[0:0]

        # India-centered Folium/Leaflet map: renders plain raster tiles + SVG
        # markers, so it works identically on machines without a WebGL2-
        # capable GPU (see src/mapview.py for why this replaced pydeck here).
        markers = []
        for level_name, color in LEVEL_COLORS.items():
            part = frame_filtered[frame_filtered["level_view"] == level_name]
            for _, row in part.iterrows():
                markers.append({
                    "lat": row["lat"], "lon": row["lon"], "color": color, "radius": 6,
                    "tooltip": (
                        f"<b>{html.escape(str(row['name']))}</b><br/>"
                        f"Risk: {row['risk_view']:.0f}/100<br/>"
                        f"Temperature: {row['temp_view']:.1f}°C<br/>"
                        f"Humidity: {row['humidity']:.0f}%<br/>"
                        f"Status: {row['level_view']}"
                    ),
                })
        markers.append({
            "lat": LAT, "lon": LON, "color": "#50c8ff", "radius": 8,
            "tooltip": f"<b>{html.escape(LOC_CITY)}</b> (city center)",
        })

        table_view = st.toggle(
            "Table view",
            value=False,
            help="Switch to a plain data table instead of the map.",
        )

        def _table_fallback():
            if len(frame_filtered):
                st.dataframe(
                    frame_filtered[["name", "risk_view", "level_view", "temp_view", "humidity"]]
                        .rename(columns={"risk_view": "risk", "level_view": "status", "temp_view": "temperature"})
                        .round(1),
                    width="stretch", hide_index=True,
                )
            else:
                st.info("No hotspots match the selected risk-level filter.")

        event = None
        if table_view or not len(frame_filtered):
            _table_fallback()
        else:
            event = render_heat_map(markers, center=(17.40, 78.47), zoom=11, height=320, key="heatshield-map")

        selected_name = st.session_state.get("selected_hotspot", "LB Nagar")
        # If a marker was clicked, its name is inside our tooltip HTML
        # ("<b>Name</b>..."); otherwise the selectbox below remains the
        # reliable interaction mechanism (works even without JS clicks).
        try:
            clicked_tooltip = (event or {}).get("last_object_clicked_tooltip")
            if clicked_tooltip:
                m = re.search(r"<b>(.*?)</b>", clicked_tooltip)
                if m:
                    candidate = html.unescape(m.group(1)).strip()
                    if candidate in frame["name"].tolist():
                        selected_name = candidate
        except Exception:
            pass

        options = frame_filtered["name"].tolist() if len(frame_filtered) else frame["name"].tolist()
        default_index = options.index(selected_name) if selected_name in options else 0
        chosen = st.selectbox("Inspect hotspot", options, index=default_index, key="hotspot-inspector")
        st.session_state["selected_hotspot"] = chosen
        row = frame[frame["name"] == chosen].iloc[0]

        st.markdown('<div class="map-legend"><span class="legend"><span class="dot" style="background:#35d889"></span>Low 0–20</span><span class="legend"><span class="dot" style="background:#ffd13b"></span>Moderate 20–40</span><span class="legend"><span class="dot" style="background:#ff9b3d"></span>High 40–60</span><span class="legend"><span class="dot" style="background:#ff4f43"></span>Severe 60–80</span><span class="legend"><span class="dot" style="background:#b05de7"></span>Extreme 80–100</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hotspot"><div class="hot-top"><div><span style="color:#ff5147">●</span> <span class="hot-name">{html.escape(str(row["name"]))}</span></div><div>{badge(row["level_view"])}</div></div><div class="hot-grid"><div><div class="hot-k">Risk Score</div><div class="hot-v">{row["risk_view"]:.0f}/100</div></div><div><div class="hot-k">Temperature</div><div class="hot-v">{row["temp_view"]:.1f}°C</div></div><div><div class="hot-k">Humidity</div><div class="hot-v">{row["humidity"]:.0f}%</div></div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="map-note">Pan and zoom the map, hover a hotspot for details, or use the hotspot selector to inspect a location. Values are prototype/sample points for the SIH demo, not live ward observations.</div></div>', unsafe_allow_html=True)

with dash_tabs[2]:
    st.markdown('<div class="panel"><div class="head"><div class="num">3</div><div>Alert Centre</div></div>', unsafe_allow_html=True)
    headline = "EXTREME HEAT RISK ALERT" if scenario_score >= 60 else ("HIGH HEAT RISK WATCH" if scenario_score >= 40 else "MONITOR CONDITIONS")
    _scenario_label = "Demo scenario" if st.session_state["demo_controls_enabled"] else "Live city"
    st.markdown(f'<div class="alert-main"><div class="alert-title">⚠ {headline}</div><div class="alert-sub">{_scenario_label} risk: {scenario_score:.0f}/100 • Review conditions regularly</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="alert-row"><div class="aicon">👷</div><div><div class="aname">Outdoor Workers</div><div class="acopy">Avoid intensive outdoor work during peak heat. Shift schedules when risk rises.</div></div><div class="priority red">High Priority</div></div><div class="alert-row"><div class="aicon">👥</div><div><div class="aname">Vulnerable Groups</div><div class="acopy">Check elderly people, children and at-risk residents.</div></div><div class="priority gold">Medium Priority</div></div><div class="alert-row"><div class="aicon">🏛</div><div><div class="aname">Authorities</div><div class="acopy">Prepare advisories, water points and cooling support.</div></div><div class="priority blue">Action Required</div></div>', unsafe_allow_html=True)
    _chan = st.session_state.get("alert_channels", [])
    _phone = st.session_state.get("alert_phone", "")
    _email = st.session_state.get("alert_email", "")
    if _chan and (_phone or _email):
        _dest = " / ".join(x for x in [_phone, _email] if x)
        st.markdown(f'<div class="channels">✅ Subscribed via {html.escape(", ".join(_chan))} &nbsp;→&nbsp; {html.escape(_dest)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="channels">Not subscribed — add your phone/email in Settings → Notification Preferences for SMS/WhatsApp/Email alerts.</div>', unsafe_allow_html=True)

    st.markdown("#### Alert delivery simulator")
    st.caption("Judge-ready simulation: validates the destination, previews the exact message, and records delivery locally. No SMS, WhatsApp message, or API request is sent.")
    demo_phone = st.text_input(
        "Demo phone number",
        value=st.session_state.get("alert_phone", ""),
        placeholder="+91 9876543210",
        key="alert_demo_phone",
        help="Use an international format for the validation demo.",
    )
    demo_channels = st.multiselect(
        "Simulated channels",
        ["SMS", "WhatsApp"],
        default=[c for c in st.session_state.get("alert_channels", ["SMS", "WhatsApp"]) if c in {"SMS", "WhatsApp"}],
        key="alert_demo_channels",
    )
    threshold = st.slider(
        "Auto-trigger threshold",
        min_value=20,
        max_value=95,
        value=int(st.session_state.get("alert_threshold", 60)),
        step=5,
        key="alert_threshold",
        help="A simulated alert is created automatically when the live risk reaches this score.",
    )
    destination_ok, destination_note = validate_alert_destination(demo_phone, demo_channels)
    if destination_ok:
        st.success(destination_note)
    else:
        st.warning(destination_note)

    preview = build_alert_message(LOC_CITY, LOC_STATE, scenario_score, scenario_level)
    preview_col, action_col = st.columns([1.35, 0.65])
    with preview_col:
        st.markdown(
            f'<div class="hotspot"><div class="hot-top"><div class="hot-name">Live message preview</div>'
            f'<div class="priority {"red" if level in {"SEVERE", "EXTREME"} else "gold"}">SIMULATION</div></div>'
            f'<div class="acopy" style="font-size:9px;color:#d9e7f5;margin-top:8px">{html.escape(preview)}</div></div>',
            unsafe_allow_html=True,
        )
    with action_col:
        auto_trigger = st.toggle(
            "Auto-trigger on threshold",
            value=st.session_state.get("alert_auto_trigger", True),
            key="alert_auto_trigger",
        )
        if st.button("Simulate send", width="stretch", disabled=not destination_ok):
            append_alert_log(
                demo_channels,
                demo_phone,
                preview,
                "Manual test",
            )
            st.success("Simulated delivery recorded.")

    if auto_trigger and scenario_score >= threshold and destination_ok:
        trigger_key = f"{LOC_STATE}:{LOC_CITY}:{threshold}:{scenario_level}"
        if st.session_state.get("last_auto_alert_key") != trigger_key:
            append_alert_log(demo_channels, demo_phone, preview, f"Auto-trigger ≥ {threshold}")
            st.session_state["last_auto_alert_key"] = trigger_key
            st.toast(f"Auto-triggered simulated {scenario_level} alert", icon="🔔")

    log_col, clear_col = st.columns([1.35, 0.65])
    with log_col:
        st.markdown("#### Alert log")
    with clear_col:
        if st.button("Clear log", width="stretch", disabled=not st.session_state.get("alert_log")):
            st.session_state["alert_log"] = []
            st.session_state.pop("last_auto_alert_key", None)
            st.rerun()
    if st.session_state.get("alert_log"):
        log_df = pd.DataFrame(st.session_state["alert_log"])
        st.dataframe(
            log_df[["time", "channel", "destination", "status", "trigger"]],
            width="stretch",
            hide_index=True,
            column_config={
                "time": "Time",
                "channel": "Channel",
                "destination": "Destination",
                "status": "Status",
                "trigger": "Trigger",
            },
        )
        with st.expander("Inspect latest simulated message"):
            st.code(st.session_state["alert_log"][0]["message"], language="text")
    else:
        st.info("No simulated deliveries yet. Use “Simulate send” or raise the live/demo risk above the threshold.")

    if st.button("ACTIVATE HEAT ACTION PLAN", width="stretch"):
        st.success("Demo action plan activated: prioritize cooling centres, drinking-water points, work-hour changes and public advisories.")
    st.markdown('</div>', unsafe_allow_html=True)

with dash_tabs[3]:
    st.markdown('<div class="panel"><div class="head"><div class="num cyan">4</div><div>Why the Risk? <span style="font-size:9px;color:#8ea4bd">ⓘ</span></div></div>', unsafe_allow_html=True)
    drivers = [("💧 Humidity", sim_humidity), ("🌡 Temperature", np.clip((sim_temperature-20)/30,0,1)*100), ("☀ Solar Radiation", np.clip(sim_radiation/1000,0,1)*100), ("🌬 Wind Speed", (1-np.clip(sim_wind/20,0,1))*100)]
    driver_html = ''.join(f'<div class="driver"><div class="drow"><span>{n}</span><span>{v:.0f}%</span></div><div class="bar"><div class="fill" style="width:{v:.0f}%"></div></div></div>' for n,v in drivers)
    insight = "High humidity is increasing evaporative difficulty, making it harder for the body to cool down. Lower wind and strong solar load add to thermal stress." if sim_humidity >= 65 else "Humidity is currently lower, so evaporative cooling is less constrained; radiation and temperature remain important drivers."
    st.markdown(f'<div class="explain"><div>{driver_html}</div><div class="insight"><div class="it">🧠 AI Insight</div><div class="ic">{insight}</div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="small" style="margin-top:5px">Established metrics shown separately: Heat Index <b>{hi:.1f}°C</b> • prototype WBGT proxy <b>{wbgt:.1f}°C</b>. These are not an official medical index.</div></div>', unsafe_allow_html=True)

with dash_tabs[4]:
    st.markdown('<div class="panel"><div class="head"><div class="num green">5</div><div>Precautions</div></div>', unsafe_allow_html=True)
    st.markdown('''<div class="prec-grid"><div class="prec"><div class="pi">💧</div><div class="pt">Stay Hydrated</div><div class="pc">Drink water regularly even if not thirsty.</div></div><div class="prec"><div class="pi">☀️</div><div class="pt">Avoid Peak Sun</div><div class="pc">Stay indoors between 12 PM – 4 PM.</div></div><div class="prec"><div class="pi">👕</div><div class="pt">Wear Light Clothes</div><div class="pc">Loose, light-coloured and breathable.</div></div><div class="prec"><div class="pi">🌳</div><div class="pt">Use Shade</div><div class="pc">Take breaks in shade or cool places.</div></div><div class="prec"><div class="pi">🧴</div><div class="pt">Sunscreen</div><div class="pc">Use SPF 30+ outdoors.</div></div><div class="prec"><div class="pi">👨‍👩‍👧</div><div class="pt">Check on Others</div><div class="pc">Help elderly, kids and vulnerable people.</div></div></div>''', unsafe_allow_html=True)
    st.button("View Detailed Guidelines →", width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

with dash_tabs[5]:
    st.markdown('<div class="panel"><div class="head"><div class="num blue">6</div><div>Smart Water Reminder</div></div>', unsafe_allow_html=True)
    if "water_liters" not in st.session_state: st.session_state.water_liters = 1.5
    if "glasses" not in st.session_state: st.session_state.glasses = 6
    if "water_interval" not in st.session_state: st.session_state.water_interval = 45
    st.session_state.water_interval = st.number_input("Reminder interval (minutes)", 15, 180, st.session_state.water_interval, 15)
    water_progress = min(st.session_state.water_liters/2.5, 1.0)
    wc1,wc2,wc3 = st.columns(3)
    with wc1:
        st.markdown(f'<div class="water"><div class="small" style="text-align:center">Next Reminder In</div><div class="ring"><div class="rn">{st.session_state.water_interval}</div><div class="ru">min</div></div><div class="small" style="text-align:center">Last drink logged: 9:41 AM</div></div>', unsafe_allow_html=True)
    with wc2:
        _full = st.session_state.glasses
        _empty = 8 - _full
        st.markdown(f'<div class="water"><div class="small">Hydration Progress</div><div class="glasses">{"🥛"*_full}{"◻"*_empty}</div><div class="wtotal">{st.session_state.glasses} / 8 <span class="small">Glasses</span></div></div>', unsafe_allow_html=True)
        st.progress(water_progress)
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("💧 I Drank Water", width="stretch"):
                st.session_state.water_liters = min(2.5, st.session_state.water_liters + .25)
                st.session_state.glasses = min(8, st.session_state.glasses + 1)
                st.rerun()
        with bcol2:
            if st.button("↺ Reset", width="stretch", help="Reset today's water intake back to 0"):
                st.session_state.water_liters = 0.0
                st.session_state.glasses = 0
                st.rerun()
    with wc3:
        st.markdown(f'<div class="water"><div class="small">Today\'s Intake</div><div class="wtotal">💧 {st.session_state.water_liters:.2f} L</div><div class="small">of 2.5 L goal</div><div style="margin-top:14px;font-size:23px;font-weight:950;color:#2f9fff;text-align:center">{water_progress*100:.0f}%</div><div class="small" style="text-align:center;margin-top:5px">Daily Goal: 2.5 Liters</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">HeatShield • AI-powered heat-risk intelligence • Live weather input from Open-Meteo • Prototype screening score, not a clinical diagnosis</div>', unsafe_allow_html=True)
