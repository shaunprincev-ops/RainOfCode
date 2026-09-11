# FloodWatch AI

## Team
- Shaunprince (@github-shaunprincev-ops)
- Deon (@github-Deon07212)
- Eeshan KS (@github-KGE8)
- Deshon Vas (@github-desvas-hub)

## What it does
FloodWatch AI is an evidence-aggregation and flood-assessment system. It takes a location and a specific flood date, retrieves relevant historical weather, public reports and geographic data, processes that evidence using Python, and presents a severity assessment with confidence and uncertainty.

## Tech stack
- **Python** — Backend logic, data processing, and flood analysis
- **Flask** — Lightweight Python web framework and REST API
- **HTML5** — Webpage structure and user interface
- **CSS3** — Styling, layout, and responsive design
- **JavaScript** — Frontend interactivity and communication with the Flask backend
- **Open-Meteo API** — Historical weather and rainfall data
- **Nominatim / OpenStreetMap** — Location geocoding and geographic data
- **Google News RSS** — Flood-related news and event evidence
- **Git & GitHub** — Version control and source-code management
- **Gunicorn** — Production server for deploying the Flask application
- **Render** — Cloud hosting and deployment

## How to run

### 1. Clone the repository
```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Start the Flask application
```bash
python app.py
```

### 6. Open the website

Open your browser and visit:

http://127.0.0.1:5000

### Deployment

The application can be deployed using Render.

**Build command:**
```bash
pip install -r requirements.txt
```

**Start command:**
```bash
gunicorn app:app
```

## Screenshots / Demo
---
