from flask import Flask, request, jsonify
from datetime import datetime, timezone          
import re
from db import insert_measurement, get_latest_measurements, get_history_for_sensor
from datetime import datetime, timezone, timedelta

def to_danish_time(utc_str):
    
    if isinstance(utc_str, datetime):
        utc_time = utc_str
    else:
        
        utc_str = str(utc_str).replace("Z", "")
        try:
            utc_time = datetime.fromisoformat(utc_str)
            utc_time = utc_time.replace(tzinfo=timezone.utc)  
        except:
            return str(utc_str)

    danish_time = utc_time + timedelta(hours=0)

    return danish_time.strftime("%d-%m-%Y %H:%M:%S")

app = Flask(__name__)

SENSOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
TEMP_PATTERN = re.compile(r"^-?\d{1,2}(\.\d{1,2})?$")

def is_temp_in_range(location, temp):
    if location == "lager":
        return 15 <= temp <= 25
    elif location == "koeleskab":
        return 2 <= temp <= 8
    return True

@app.post("/api/measurements")
def create_measurement():
    data = request.get_json(force=True)

    sensor_id = data.get("sensor_id")

    temp_str = data.get("temperatur") or data.get("temperature")
    location = data.get("location")

    if not sensor_id or not SENSOR_ID_PATTERN.match(str(sensor_id)):
        return jsonify({"error": "invalid sensor_id"}), 400

    if temp_str is None or not TEMP_PATTERN.match(str(temp_str)):
        return jsonify({"error": "invalid temperature format"}), 400

    try:
        temp_float = float(temp_str)
    except ValueError:
        return jsonify({"error": "temperature must be a number"}), 400

    if not location:
        return jsonify({"error": "location is required"}), 400

    
    ts = datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z"
    alarm_flag = not is_temp_in_range(location, temp_float)

    insert_measurement(sensor_id, ts, temp_float, location, alarm_flag)

    return jsonify({
        "status": "ok",
        "alarm": alarm_flag,
        "timestamp": ts
    }), 201


@app.get("/api/measurements/latest")
def latest():
    rows = get_latest_measurements()
    for row in rows:
        if "timestamp" in row and row["timestamp"]:
            row["timestamp"] = to_danish_time(row["timestamp"])
    return jsonify(rows)

@app.get("/api/measurements/history/<sensor_id>")
def history(sensor_id):
    rows = get_history_for_sensor(sensor_id)
    for row in rows:
        if "timestamp" in row and row["timestamp"]:
            row["timestamp"] = to_danish_time(row["timestamp"])
    return jsonify(rows)

@app.get("/")
def index():
    return """
    <h1>IOT Apotek – Temperatur API</h1>
    <p>POST målinger til <code>/api/measurements</code></p>
    <p>Se seneste målinger på <code>/api/measurements/latest</code></p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)