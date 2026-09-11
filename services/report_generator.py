def build_report(result):
    w = result["weather"]
    rain = w.get("event_day_rain_mm")
    rain_text = f"{rain} mm" if rain is not None else "Unavailable"
    window = result["analysis_window"]
    news_count = len(result["news"])

    return {
        "overview": (
            f"FloodWatch AI analyzed {result['display_name']} for the flood event on "
            f"{result['flood_date']} ({result['flood_time']})."
        ),
        "severity": (
            f"Severity classification: {result['severity']} "
            f"(event evidence score {result['severity_score']}/100)."
        ),
        "weather": (
            f"Rainfall on the selected event date: {rain_text}. "
            f"Weather analysis window: {window['start']} to {window['end']}."
        ),
        "evidence": (
            f"{news_count} event-window public report(s) were retained. "
            "Publication date is kept separate from the flood event date."
        ),
        "building": (
            "Building-level damage is not inferred from area-level flooding. "
            "A building requires location-specific, event-relevant evidence."
        ),
        "uncertainty": (
            "Current/future weather data is excluded from historical event scoring. "
            "OpenStreetMap is used only for geographic context, not as historical flood evidence."
        ),
    }
