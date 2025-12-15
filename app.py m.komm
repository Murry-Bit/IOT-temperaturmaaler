# Importerer Flask-frameworket og hjælpefunktioner til HTTP requests og JSON-svar
from flask import Flask, request, jsonify
# Importerer datetime-typer til håndtering af tid og tidszoner
from datetime import datetime, timezone, timedelta
# Importerer regex-modulet til validering af input
import re
# Importerer database-funktioner fra db.py
from db import insert_measurement, get_latest_measurements, get_history_for_sensor

# Konverterer et UTC-timestamp til dansk tidsformat (streng)
def to_danish_time(utc_str):

    # Hvis input allerede er et datetime-objekt
    if isinstance(utc_str, datetime):
        utc_time = utc_str
    else:
        # Fjerner evt. 'Z' fra ISO-timestamp
        utc_str = str(utc_str).replace("Z", "")
        try:
            # Konverterer streng til datetime
            utc_time = datetime.fromisoformat(utc_str)

            # Sætter tidszonen til UTC
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        except:
            # Hvis konvertering fejler, returneres input som tekst
            return str(utc_str)

    # Lægger forskel til dansk tid (0 her – placeholder)
    danish_time = utc_time + timedelta(hours=0)

    # Returnerer tidspunkt i dansk læsevenligt format
    return danish_time.strftime("%d-%m-%Y %H:%M:%S")

# Opretter Flask-applikationen
app = Flask(__name__)

# Regex til gyldigt sensor-id (3–30 tegn, bogstaver, tal og _)
SENSOR_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")

# Regex til temperatur (fx -5, 12, 20.5)
TEMP_PATTERN = re.compile(r"^-?\d{1,2}(\.\d{1,2})?$")

# Tjekker om temperatur er inden for tilladt område baseret på location
def is_temp_in_range(location, temp):
    if location == "lager":
        return 15 <= temp <= 25
    elif location == "koeleskab":
        return 2 <= temp <= 8

    # Hvis location ikke er kendt, accepteres altid
    return True

# Endpoint til at modtage nye temperaturmålinger
@app.post("/api/measurements")
def create_measurement():

    # Henter JSON-data fra request body
    data = request.get_json(force=True)

    # Henter sensor-id
    sensor_id = data.get("sensor_id")

    # Henter temperatur (accepterer både dansk og engelsk nøgle)
    temp_str = data.get("temperatur") or data.get("temperature")

    # Henter location (fx lager eller koeleskab)
    location = data.get("location")

    # Validerer sensor-id
    if not sensor_id or not SENSOR_ID_PATTERN.match(str(sensor_id)):
        return jsonify({"error": "invalid sensor_id"}), 400

    # Validerer temperatur-format
    if temp_str is None or not TEMP_PATTERN.match(str(temp_str)):
        return jsonify({"error": "invalid temperature format"}), 400

    # Forsøger at konvertere temperatur til float
    try:
        temp_float = float(temp_str)
    except ValueError:
        return jsonify({"error": "temperature must be a number"}), 400

    # Location er påkrævet
    if not location:
        return jsonify({"error": "location is required"}), 400

    # Opretter UTC-timestamp i ISO-format
    ts = datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z"

    # Alarm aktiveres hvis temperaturen er uden for tilladt interval
    alarm_flag = not is_temp_in_range(location, temp_float)

    # Gemmer målingen i databasen
    insert_measurement(sensor_id, ts, temp_float, location, alarm_flag)

    # Returnerer succes-respons
    return jsonify({
        "status": "ok",
        "alarm": alarm_flag,
        "timestamp": ts
    }), 201


# Endpoint der returnerer seneste målinger
@app.get("/api/measurements/latest")
def latest():

    # Henter seneste målinger fra databasen
    rows = get_latest_measurements()

    # Konverterer timestamps til dansk tid
    for row in rows:
        if "timestamp" in row and row["timestamp"]:
            row["timestamp"] = to_danish_time(row["timestamp"])

    return jsonify(rows)


# Endpoint der returnerer historik for én sensor
@app.get("/api/measurements/history/<sensor_id>")
def history(sensor_id):

    # Henter alle målinger for sensor
    rows = get_history_for_sensor(sensor_id)

    # Konverterer timestamps til dansk tid
    for row in rows:
        if "timestamp" in row and row["timestamp"]:
            row["timestamp"] = to_danish_time(row["timestamp"])

    return jsonify(rows)

# Forside / test-endpoint
@app.get("/")
def index():
    return """
    <h1>IOT Apotek – Temperatur API</h1>
    <p>POST målinger til <code>/api/measurements</code></p>
    <p>Se seneste målinger på <code>/api/measurements/latest</code></p>
    """

# Starter Flask-serveren hvis filen køres direkte
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
