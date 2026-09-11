import re
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import feedparser
import requests

HEADERS = {"User-Agent": "FloodWatchAI/1.0 (educational project)"}
TIMEOUT = 20


def _get(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response


def _parse_date(value):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).date()
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except Exception:
            continue
    return None


def _event_window(flood_date, flood_time=""):
    event = datetime.strptime(flood_date, "%Y-%m-%d").date()
    # If no exact time is known, use the flood day plus the preceding 24 hours.
    # We never extend the weather window into a future day.
    start = event - timedelta(days=1)
    end = event
    exact = bool(flood_time)
    return event, start, end, exact


def geocode(location):
    data = _get(
        "https://nominatim.openstreetmap.org/search",
        {"q": location, "format": "jsonv2", "limit": 1},
    ).json()
    if not data:
        raise ValueError("Location could not be found.")
    return {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"]),
        "display_name": data[0].get("display_name", location),
    }


def get_historical_weather(lat, lon, flood_date, flood_time=""):
    """Retrieve weather for the selected event period, never the current period."""
    event, start, end, exact = _event_window(flood_date, flood_time)
    today = date.today()

    if start > today:
        return {
            "available": False,
            "reason": "The selected flood period is in the future; historical observations do not exist yet.",
            "source": "Open-Meteo Historical Weather API",
            "event_date": flood_date,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        }

    # Open-Meteo's archive endpoint is used for historical observations.
    data = _get(
        "https://archive-api.open-meteo.com/v1/archive",
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": min(end, today).isoformat(),
            "hourly": "precipitation,rain",
            "timezone": "auto",
        },
    ).json()

    times = data.get("hourly", {}).get("time", [])
    rain = data.get("hourly", {}).get("rain", [])
    precipitation = data.get("hourly", {}).get("precipitation", [])

    rows = []
    for i, timestamp in enumerate(times):
        try:
            ts = datetime.fromisoformat(timestamp)
        except ValueError:
            continue
        if ts.date() <= event:
            rows.append({
                "time": timestamp,
                "rain_mm": rain[i] if i < len(rain) else None,
                "precipitation_mm": precipitation[i] if i < len(precipitation) else None,
            })

    rain_values = [r["rain_mm"] for r in rows if r["rain_mm"] is not None]
    event_day = [r for r in rows if r["time"][:10] == flood_date]
    event_rain = [r["rain_mm"] for r in event_day if r["rain_mm"] is not None]

    return {
        "available": True,
        "source": "Open-Meteo Historical Weather API",
        "event_date": flood_date,
        "event_time": flood_time or "Unknown",
        "period_start": start.isoformat(),
        "period_end": min(end, today).isoformat(),
        "analysis_basis": "Historical observations only; no future hours are used.",
        "rain_24h_mm": round(sum(rain_values), 1) if rain_values else None,
        "event_day_rain_mm": round(sum(event_rain), 1) if event_rain else None,
        "max_hourly_rain_mm": round(max(rain_values), 1) if rain_values else None,
        "hourly": rows,
    }


def get_news(location, flood_date):
    """Collect event-date-focused RSS results and retain publication metadata."""
    event, start, end, _ = _event_window(flood_date)
    # Allow a short post-event publication window because reports can be published later.
    publication_end = event + timedelta(days=2)
    queries = [
        f'"{location}" flood after:{start.isoformat()} before:{(event + timedelta(days=1)).isoformat()}',
        f'"{location}" flooding after:{start.isoformat()} before:{(publication_end + timedelta(days=1)).isoformat()}',
        f'"{location}" inundation after:{start.isoformat()} before:{(publication_end + timedelta(days=1)).isoformat()}',
    ]

    results = {}
    for query in queries:
        url = "https://news.google.com/rss/search?q=" + quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = re.sub("<[^>]+>", "", entry.get("summary", ""))
            published = entry.get("published", "")
            published_date = _parse_date(published)
            # Publication can be up to two days after the event, but not before the
            # beginning of the event window. This prevents unrelated current articles.
            if published_date and not (start <= published_date <= publication_end):
                continue
            key = entry.get("link") or title
            results[key] = {
                "title": title,
                "summary": summary[:700],
                "url": entry.get("link", ""),
                "published": published,
                "published_date": published_date.isoformat() if published_date else None,
                "event_date": flood_date,
                "event_date_basis": "Selected flood event date; article must be temporally relevant.",
                "type": "news",
                "temporal_relevance": "high" if published_date and published_date >= event else "medium",
                "confidence": "medium",
            }

    return list(results.values())[:20]


def get_osm_context(lat, lon):
    query = f"""
    [out:json][timeout:20];
    (
      way(around:1800,{lat},{lon})[highway];
      way(around:1800,{lat},{lon})[building];
      way(around:1800,{lat},{lon})[waterway];
    );
    out tags center;
    """
    try:
        data = _get("https://overpass-api.de/api/interpreter", {"data": query}).json()
    except Exception:
        return {"roads": [], "buildings": [], "waterways": []}

    roads, buildings, waterways = [], [], []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        center = el.get("center", {})
        obj = {"name": tags.get("name", "Unnamed"), "lat": center.get("lat"), "lon": center.get("lon")}
        if "highway" in tags:
            roads.append(obj)
        elif "building" in tags:
            buildings.append(obj)
        elif "waterway" in tags:
            waterways.append(obj)
    return {"roads": roads[:100], "buildings": buildings[:100], "waterways": waterways[:50]}


def severity_from_evidence(weather, news):
    rain = weather.get("event_day_rain_mm")
    rain = rain if rain is not None else 0
    flood_words = sum(
        1 for x in news
        if any(w in (x["title"] + " " + x["summary"]).lower()
               for w in ["severe", "submerged", "inundat", "evacuat", "waterlogged", "flood"])
    )
    score = min(100, rain * 1.2 + flood_words * 7)
    if score >= 70:
        label = "Severe"
    elif score >= 45:
        label = "High"
    elif score >= 20:
        label = "Moderate"
    else:
        label = "Low"
    return label, round(score)


def analyze_location(location, flood_date="", flood_time=""):
    if not flood_date:
        raise ValueError("A flood date is required so the system can retrieve event-specific data.")
    try:
        datetime.strptime(flood_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Flood date must be in YYYY-MM-DD format.")

    geo = geocode(location)
    weather = get_historical_weather(geo["lat"], geo["lon"], flood_date, flood_time)
    news = get_news(location, flood_date)
    osm = get_osm_context(geo["lat"], geo["lon"])
    severity, score = severity_from_evidence(weather, news)

    evidence_count = len(news)
    confidence = min(95, 25 + evidence_count * 3 + (25 if weather.get("available") else 0))

    areas = [{
        "name": geo["display_name"].split(",")[0],
        "severity": severity,
        "score": score,
        "water_depth": "Unknown — no reliable ground-level measurement found",
        "roads_affected": "Not directly verified",
        "buildings_affected": "Not directly verified",
        "evidence": evidence_count,
        "confidence": confidence,
        "note": "Severity uses evidence tied to the selected flood event; it is not a direct flood-depth measurement.",
    }]

    return {
        "location": location,
        "display_name": geo["display_name"],
        "lat": geo["lat"],
        "lon": geo["lon"],
        "flood_date": flood_date,
        "flood_time": flood_time or "Unknown",
        "analysis_window": {
            "start": (datetime.strptime(flood_date, "%Y-%m-%d").date() - timedelta(days=1)).isoformat(),
            "end": flood_date,
            "future_data_used": False,
        },
        "severity": severity,
        "severity_score": score,
        "confidence": confidence,
        "weather": weather,
        "news": news,
        "areas": areas,
        "osm": osm,
        "limitations": [
            "Exact building-level flood depth was not available from the collected sources.",
            "Flooding in an area does not prove that every building is damaged.",
            "Historical observations are used instead of current/forecast weather.",
            "Later-published reports may describe the selected event, but their publication date is shown separately.",
            "OpenStreetMap provides current geographic context and is not historical flood evidence.",
        ],
    }


def analyze_building(location, building, flood_date, flood_time=""):
    if not flood_date:
        raise ValueError("Flood date is required for building-level event analysis.")
    geo = geocode(f"{building}, {location}")
    nearby = get_news(f"{building}, {location}", flood_date)
    return {
        "building": building,
        "location": geo["display_name"],
        "lat": geo["lat"],
        "lon": geo["lon"],
        "flood_date": flood_date,
        "flood_time": flood_time or "Unknown",
        "flood_status": "Unconfirmed",
        "ground_floor": "Unknown",
        "water_depth": "Unknown",
        "visible_damage": "Unable to determine without a relevant photograph or verified event-specific report.",
        "confidence": 25 if not nearby else 45,
        "evidence": nearby[:6],
        "explanation": (
            "The system found the building location and searched for evidence tied to the selected flood date. "
            "It will not claim building damage from nearby flooding alone."
        ),
    }
