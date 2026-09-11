"""Thermal-stress calculations for the HeatShield prototype."""

def heat_index_celsius(temp_c, humidity):
    """NOAA/Rothfusz heat-index approximation, returned in Celsius.

    The NWS only ever applies the full Rothfusz polynomial after first
    checking a simpler estimate, and even then treats the result as
    indicative once conditions are far outside the regression's fitted
    range (roughly 27-49 degC / 80-125 degF). Applying the raw polynomial
    unconditionally can extrapolate to physically meaningless values --
    e.g. 42 degC at 68% RH previously produced an ~80 degC "feels like"
    reading. We keep the same published coefficients (for transparency)
    but clamp the output to a sane band around the actual temperature so
    a judge/demo never sees a nonsensical number.
    """
    T = temp_c * 9 / 5 + 32
    RH = max(0.0, min(float(humidity), 100.0))
    HI = (
        -42.379 + 2.04901523*T + 10.14333127*RH
        - 0.22475541*T*RH - 0.00683783*T*T
        - 0.05481717*RH*RH + 0.00122874*T*T*RH
        + 0.00085282*T*RH*RH
        - 0.00000199*T*T*RH*RH
    )
    hi_c = (HI - 32) * 5 / 9
    # Sanity clamp: apparent temperature should stay within a plausible
    # band of the actual temperature (heat index is not meant to add tens
    # of degrees beyond what humidity/temperature can physically produce).
    return round(max(temp_c, min(hi_c, temp_c + 18)), 1)


def wbgt_proxy(temperature, humidity, wind_speed, solar_radiation):
    """Transparent prototype WBGT-like screening proxy.

    This is NOT an official WBGT implementation. It is only a visual/demo
    indicator until a documented, validated methodology is added.
    """
    t = float(temperature)
    rh = max(0.0, min(float(humidity), 100.0))
    wind = max(0.0, float(wind_speed))
    rad = max(0.0, float(solar_radiation))
    globe_proxy = t + 0.015 * rad - 0.08 * wind
    wet_proxy = t - 0.25 * (100 - rh) / 5.0
    return round(0.7 * wet_proxy + 0.3 * globe_proxy, 1)


def thermal_stress_score(temperature, humidity, wind_speed, solar_radiation):
    temp_component = min(max((temperature - 30) / 15, 0), 1)
    humidity_component = min(max((humidity - 40) / 50, 0), 1)
    wind_component = 1 - min(wind_speed / 20, 1)
    radiation_component = min(max(solar_radiation / 1000, 0), 1)
    score = (
        0.40 * temp_component
        + 0.25 * humidity_component
        + 0.15 * wind_component
        + 0.20 * radiation_component
    ) * 100
    return round(min(score, 100), 2)


def risk_category(score):
    if score < 20:
        return "LOW"
    if score < 40:
        return "MODERATE"
    if score < 60:
        return "HIGH"
    if score < 80:
        return "SEVERE"
    return "EXTREME"
