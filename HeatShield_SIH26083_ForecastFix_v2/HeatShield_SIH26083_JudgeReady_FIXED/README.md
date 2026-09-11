# HEATSHIELD SIH26083 (Judge-Ready Build)

Self-contained Streamlit prototype for Hyderabad heat-risk intelligence.

## Run in VS Code PowerShell

Open THIS folder (the folder containing `app.py`). Then run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Or double-click `run_heatshield.bat`.

## Important

Do not open a parent folder and expect `data/` to be found elsewhere.
`app.py` uses an absolute path based on its own location, and the required
`data/sample_hotspots.csv` is included in this package.

The hotspot CSV's `temperature`/`humidity` columns are prototype/demo
seed values used to give each neighbourhood a relative offset from the
live citywide reading — replace with validated Hyderabad ward data before
claiming live hyperlocal measurements. (The CSV's original `risk`/`category`
columns are no longer used for display — see "What changed" below.)

## Optional: run the API separately

`api/main.py` is a small FastAPI service, independent of the Streamlit
dashboard. It is **not** started by `run_heatshield.bat`. To run it:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

Then visit `http://127.0.0.1:8000/risk/hyderabad`.

## Map notes

The map now uses `folium` (Leaflet.js) instead of `pydeck`/`deck.gl`. This
was changed because deck.gl needs a real WebGL2 context in the browser —
on VMs, remote-desktop/RDP sessions, or machines with hardware acceleration
disabled, that produced a blank, garbled, or distorted oval/globe render
instead of a flat India map. Folium renders plain raster map tiles and
SVG/canvas markers, so it works the same on every machine regardless of
GPU support, with no WebGL dependency at all.

It uses standard OpenStreetMap tiles, which are free with no API key —
note that Carto's tile styles (used in earlier builds) now require one as
of a recent policy change, which is part of why this switched providers.

- Toggle **"Table view"** above any map for a plain data-table alternative.
- If a map area ever renders blank, it's almost always a lack of internet
  access to fetch map tiles (OpenStreetMap's tile servers), not a
  GPU/WebGL issue — check your connection rather than `chrome://gpu`.

## What changed in this build

- **Header location is now a real whole-of-India picker.** The static
  "⌖ Hyderabad, Telangana ▾" chip is now two live selectboxes (State/UT →
  City/Town) backed by the same `INDIA_LOCATIONS` dataset as the India Map
  tab. Changing it re-fetches live weather for that city and recomputes the
  AI Heat Risk Index, forecast, and Alert Centre for it. Hyderabad's
  neighbourhood-level hotspot map (Tab 2) still shows its full hyperlocal
  detail; any other selected city shows a live single-point city view with a
  clear note that ward-level hotspots are currently a Hyderabad-pilot
  dataset. Also fixed a caching bug where the weather fetch was keyed on no
  arguments at all, so switching location would have silently kept serving
  the first city's cached reading.

- **Fixed a real "feels like" bug**: the classic Rothfusz heat-index
  polynomial mathematically explodes outside its fitted range — e.g. a
  realistic Hyderabad pre-monsoon reading of 42°C / 68% RH previously
  displayed an absurd **"Heat Index 80°C"** in the "Why the Risk?" tab.
  `src/thermal.py` now clamps the output to a physically sane band around
  the actual temperature, so the number stays credible in front of judges
  no matter what the live weather does on demo day.
- Added `JUDGES_PRESENTATION_GUIDE.md` — a one-stop briefing mapping every
  panel of the dashboard to standard hackathon judging criteria, plus a
  suggested 3-minute walkthrough script and anticipated Q&A.
- Verified all Python modules compile and the pure-logic risk engine
  (`thermal.py`, `vulnerability.py`, `risk_engine.py`) behaves correctly
  across edge cases (0%, 100%, extreme heat, extreme cold).

## What changed from V13/V14

- **AI Risk gauge** now actually reflects the score (needle angle and arc
  color used to be hardcoded and never moved).
- **Map hotspot risk** is now computed with the same `calculate_risk()`
  engine as the headline score, anchored to today's live temperature and
  Open-Meteo's real forecast trend — instead of a static CSV number plus an
  arbitrary "+2 points per forecast day."
- **`api/main.py`** now fetches live weather (it was fully hardcoded) and
  uses the same vulnerability constants as the dashboard (previously
  `healthcare_access` differed between the two, so they could report
  different risk scores for the same city).
- **Current solar radiation** is now read from Open-Meteo's `current` block
  instead of the first hourly value (which was usually a stale midnight
  reading).
- **Sidebar demo sliders** now show their effect (a "Demo scenario" delta
  line) instead of being computed and silently discarded.
- Added a **Table view** toggle as a non-WebGL fallback for the map, and
  pinned an explicit basemap style instead of relying on theme auto-detect.
- Removed unused `.map-wrap` CSS and added `fastapi`/`uvicorn` to the
  preflight dependency check.
- Moved the **"Refresh weather"** button out of the sidebar into the main
  dashboard header, next to the "Last updated" time.
- Added a **simulated SMS/WhatsApp alert workflow** in Alert Centre: country-code
  phone validation, live message preview, manual simulated delivery, a
  session-only alert log, and an auto-trigger toggle with an adjustable risk
  threshold. It never calls a messaging provider or requires API keys.
- Demo Controls now include a **temperature slider**. Raising it recomputes the
  demo scenario score, risk drivers, alert preview, and threshold auto-trigger
  while keeping the live score visible for comparison.
- Added a **"Reset"** button next to "I Drank Water" in the Smart Water
  Reminder panel to clear today's intake back to 0, and made the glass icons
  (🥛/◻) reflect the actual count instead of a fixed image.
