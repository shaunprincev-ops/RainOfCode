from flask import Flask, render_template, request, jsonify
from services.data_collection import analyze_location, analyze_building
from services.report_generator import build_report

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/analyze-flood")
def api_analyze_flood():
    data = request.get_json(silent=True) or {}
    location = (data.get("location") or "").strip()
    flood_date = (data.get("flood_date") or "").strip()
    flood_time = (data.get("flood_time") or "").strip()

    if not location:
        return jsonify({"error": "Please enter a location."}), 400
    if not flood_date:
        return jsonify({"error": "Please enter the flood date. Historical event analysis requires a date."}), 400

    try:
        result = analyze_location(location, flood_date, flood_time)
        result["report"] = build_report(result)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Analysis failed: {exc}"}), 500

@app.post("/api/building-analysis")
def api_building_analysis():
    data = request.get_json(silent=True) or {}
    location = (data.get("location") or "").strip()
    building = (data.get("building") or "").strip()
    flood_date = (data.get("flood_date") or "").strip()
    flood_time = (data.get("flood_time") or "").strip()

    if not location or not building:
        return jsonify({"error": "Enter both a location and building/address."}), 400
    if not flood_date:
        return jsonify({"error": "Analyze the flood date first so building evidence is tied to the same event."}), 400

    try:
        return jsonify(analyze_building(location, building, flood_date, flood_time))
    except Exception as exc:
        return jsonify({"error": f"Building analysis failed: {exc}"}), 500

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)