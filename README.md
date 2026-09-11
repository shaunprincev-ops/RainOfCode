# FloodWatch AI

An educational Flask prototype for evidence-based flood assessment.

## What works now

- Location search/geocoding with OpenStreetMap Nominatim
- Public flood-related news RSS collection
- Recent precipitation information from Open-Meteo
- Nearby roads/buildings/waterways from OpenStreetMap Overpass
- Evidence-based severity estimate
- Interactive Leaflet map
- Area summary
- Building lookup
- Source links
- Clear uncertainty labels

## Run in VS Code

Open the FloodWatch folder in VS Code, then in the terminal:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install packages:

```bash
pip install -r requirements.txt
```

Start:

```bash
python app.py
```

Open:

http://127.0.0.1:5000

## Important

This version intentionally does not invent building damage or water-depth measurements. AI/vision and satellite providers can be added later through the service layer.

Public services can have usage limits. Use their terms and attribution requirements, and do not scrape sites that prohibit automated access.
