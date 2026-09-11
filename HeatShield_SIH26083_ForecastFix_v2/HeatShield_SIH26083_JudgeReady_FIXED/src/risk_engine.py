"""Combine thermal stress and vulnerability into a prototype risk score."""
from src.thermal import thermal_stress_score, risk_category
from src.vulnerability import vulnerability_score


def calculate_risk(
    temperature, humidity, wind_speed, solar_radiation,
    population_density, elderly_percentage,
    outdoor_worker_percentage, healthcare_access,
):
    thermal = thermal_stress_score(
        temperature, humidity, wind_speed, solar_radiation
    )
    vulnerability = vulnerability_score(
        population_density,
        elderly_percentage,
        outdoor_worker_percentage,
        healthcare_access,
    )
    overall = round(0.65 * thermal + 0.35 * vulnerability, 2)
    return {
        "thermal_stress": thermal,
        "vulnerability": vulnerability,
        "overall_risk": overall,
        "risk_category": risk_category(overall),
    }
