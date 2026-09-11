# HEATSHIELD (SIH26083) — Judge Presentation Guide

One-line pitch: **HeatShield turns live weather + local vulnerability data into
a real-time, hyperlocal heat-risk score and actionable warning system — first
for Hyderabad, architected to scale to any Indian district.**

Use this document to rehearse the demo and to answer the questions judges
almost always ask at SIH. Nothing here needs to be memorised verbatim — it is
a map from *what the judges are scoring* to *which screen proves it*.

---

## 1. How this maps to standard SIH judging criteria

| Judging criterion | Where it shows up in HeatShield | What to say |
|---|---|---|
| **Innovation / uniqueness** | Tab 4 "Why the Risk?" — transparent, explainable driver breakdown (humidity/temp/wind/radiation) instead of a black-box score | "Most heat apps show one number. We show *why* — an AI-style explainability layer built on physical drivers, not a hidden model." |
| **Technical complexity & correctness** | `src/risk_engine.py` combines a thermal-stress model (`thermal.py`) with a socio-demographic vulnerability model (`vulnerability.py`); live weather via Open-Meteo; same engine reused identically by the Streamlit dashboard *and* the FastAPI service | "The dashboard and the API call the exact same `calculate_risk()` function — so a city dashboard and a third-party integration (e.g. a government SMS gateway) never disagree." |
| **Feasibility of implementation** | Runs today on live public weather data (Open-Meteo, no API key needed), degrades gracefully to a labelled fallback if the network drops, works over remote desktop via the built-in Table View | "Nothing here depends on unreleased tech. It runs on a laptop right now." |
| **Scalability** | Tab "India Map" already covers all 36 states/UTs with a drill-down to district → city, using one batched API call instead of 36 separate ones | "The Hyderabad build is the pilot. `src/india_locations.py` is a data file, not a code change — extending to every district is a data-entry task, not a redesign." |
| **Impact / social relevance** | Tab 3 "Alert Centre" segments messaging by outdoor workers, vulnerable groups (elderly/children), and authorities; Tab 6 water reminder nudges individual behaviour | "We target the three groups the National Disaster Management Authority's Heat Action Plans call out specifically: outdoor labour, vulnerable residents, and local authorities." |
| **UI/UX & presentation clarity** | Single-page tabbed command centre, colour-coded 5-level risk scale (LOW→EXTREME) used consistently across every chart, map and badge | "One colour language, everywhere — a judge or a district officer can read risk level from colour alone." |
| **Sustainability / honesty** | README explicitly labels which numbers are *live* (Open-Meteo temperature/humidity/wind/radiation) vs *prototype/demo* (hotspot CSV offsets, WBGT proxy, vulnerability constants) | "We'd rather tell you exactly which numbers are real today and which need validated ward-level data before deployment, than oversell it." |

---

## 2. Suggested 3-minute demo script

1. **Open on Dashboard, Tab 1** (10s): point at the live "● LIVE" badge and
   the AI Heat Risk Index gauge. Say the score and level out loud — it's
   computed from *today's* real Hyderabad weather, not a canned demo value.
2. **Tab 2 — Live Map** (30s): show the 12 Hyderabad hotspots colour-coded by
   risk, click one (e.g. Charminar or LB Nagar — usually the hottest), flip
   the forecast-window radio to "+2 Days" to show risk trending with the
   real forecast. Mention the Table View toggle exists for judges on
   restrictive laptops/VMs where WebGL maps sometimes fail.
3. **Tab 4 — Why the Risk?** (30s): this is the "innovation" beat — show the
   driver bars and the AI Insight sentence changing based on humidity.
4. **Tab 3 — Alert Centre** (20s): show the three audience-specific message
   cards (outdoor workers / vulnerable groups / authorities) and the
   notification-channel subscription flow in Settings.
5. **India Map page** (30s): zoom out to the national view, use the
   State → District → City drill-down to jump to the judges' own city live,
   in front of them — this lands well because it's not scripted.
6. **Close** (20s): state the roadmap — validated ward-level sensor data,
   real SMS/WhatsApp delivery, and IMD (India Meteorological Department)
   data integration alongside Open-Meteo.

---

## 3. Anticipated judge questions — honest, prepared answers

**"Is this using real data or is it hardcoded?"**
Live current weather (temperature, humidity, wind, solar radiation) comes
from the Open-Meteo public API for whichever location is selected — this is
real and updates on every refresh. The Hyderabad neighbourhood-level hotspot
*offsets* (why Charminar reads a bit hotter than Gachibowli) are prototype
seed values standing in for validated ward-level sensor data, which is
explicitly called out in the README rather than presented as measured.

**"What's the actual algorithm behind the risk score?"**
`overall_risk = 0.65 × thermal_stress + 0.35 × vulnerability`. Thermal stress
weighs temperature, humidity, wind (cooling) and solar radiation. Vulnerability
weighs population density, % elderly, % outdoor workers and healthcare access.
Both are transparent, documented formulas in `src/thermal.py` and
`src/vulnerability.py` — not a black box, and easy to recalibrate once real
epidemiological/ward data is available.

**"Why isn't this a certified WBGT (Wet Bulb Globe Temperature) reading?"**
WBGT requires a physical black-globe/wet-bulb sensor; ours is a transparent
proxy formula clearly labelled "not an official medical index" everywhere it
appears, used only to add a secondary, more occupational-health-oriented
signal alongside the standard Heat Index.

**"How would this actually reach an outdoor worker with no smartphone?"**
The Alert Centre's SMS/WhatsApp channel selection is the intended delivery
path for the pilot; the production plan is to integrate with an authorized
government SMS gateway / Common Alerting Protocol feed (the same channel
State Disaster Management Authorities already use for Heat Action Plan
advisories), not a general consumer push notification.

**"What happens if the internet or the weather API goes down mid-demo?"**
Both the dashboard and the API fall back to a clearly-labelled demo-safe
reading (never a silent stale value) — try turning off Wi-Fi and refreshing
to show the judges the fallback banner if you want to prove robustness live.

---

## 4. Known limitations (say these before a judge finds them)

- Hyderabad hotspot temperatures are prototype offsets, not live per-ward
  sensors — flagged explicitly in the dashboard and README.
- The WBGT-style figure is a labelled proxy, not a certified WBGT instrument
  reading.
- SMS/WhatsApp/Email delivery in Settings is a UI mock for the pilot; no
  message is actually sent yet.
- National coverage currently ships ~1 representative city per district per
  state (extendable via a data file, not a redesign).

Being upfront about these signals engineering maturity rather than hiding
gaps — SIH judges consistently reward teams who know exactly what's real vs.
prototype in their own build.

---

## 5. Tech stack, one line each

- **Frontend/dashboard**: Streamlit + custom CSS, PyDeck (deck.gl) for maps
- **Backend logic**: Python — `thermal.py` (heat-index/WBGT-proxy),
  `vulnerability.py`, `risk_engine.py` (single source of truth for scoring)
- **API**: FastAPI + Uvicorn, `/risk/hyderabad`, same scoring engine as the UI
- **Live data**: Open-Meteo forecast API (no key required), 5-day hourly +
  daily forecast, Asia/Kolkata timezone
- **Coverage data**: `src/india_locations.py` — 36 states/UTs, drill-down to
  district → city

---

## 6. Running it before you walk in

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
or double-click `run_heatshield.bat`. Do a live refresh in the room 5–10
minutes before you present so the "Last updated" time looks current, and
have Wi-Fi confirmed working at the venue — the whole pitch is that the
numbers are real.
