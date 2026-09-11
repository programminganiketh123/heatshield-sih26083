from fastapi import FastAPI
import requests

from src.risk_engine import calculate_risk

app = FastAPI(
    title="HeatShield API",
    description="Extreme Heat and Human Thermal Stress API",
    version="1.0",
)

LAT, LON = 17.3850, 78.4867

# Same prototype vulnerability constants used by the Streamlit dashboard
# (app.py). These previously drifted out of sync (the dashboard used
# healthcare_access=72, this API used 40), which meant the API and the
# dashboard could report two different risk scores for the same city.
POPULATION_DENSITY = 16000
ELDERLY_PERCENTAGE = 18
OUTDOOR_WORKER_PERCENTAGE = 32
HEALTHCARE_ACCESS = 72

# Demo-safe fallback used only if the live weather call fails, matching the
# fallback values in app.py so the two stay consistent even when offline.
FALLBACK_WEATHER = {
    "temperature_2m": 39.5,
    "relative_humidity_2m": 68.0,
    "wind_speed_10m": 6.0,
    "shortwave_radiation": 850.0,
}


def fetch_live_weather():
    """Fetch current Hyderabad conditions from Open-Meteo.

    Previously this endpoint always returned a hardcoded temperature/humidity
    regardless of real conditions, despite being described as a live API.
    """
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LAT, "longitude": LON,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation",
            "timezone": "Asia/Kolkata",
        },
        timeout=12,
    )
    r.raise_for_status()
    return r.json()["current"]


@app.get("/")
def home():
    return {"system": "HeatShield", "status": "online"}


@app.get("/risk/hyderabad")
def hyderabad_risk():
    is_live = True
    try:
        current = fetch_live_weather()
    except Exception:
        current = FALLBACK_WEATHER
        is_live = False

    result = calculate_risk(
        temperature=current["temperature_2m"],
        humidity=current["relative_humidity_2m"],
        wind_speed=current["wind_speed_10m"],
        solar_radiation=max(current.get("shortwave_radiation") or 0.0, 250),
        population_density=POPULATION_DENSITY,
        elderly_percentage=ELDERLY_PERCENTAGE,
        outdoor_worker_percentage=OUTDOOR_WORKER_PERCENTAGE,
        healthcare_access=HEALTHCARE_ACCESS,
    )
    return {
        "location": "Hyderabad",
        "live_weather": is_live,
        "inputs": current,
        **result,
    }
