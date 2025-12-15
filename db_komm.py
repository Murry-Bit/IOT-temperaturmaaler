# PostgreSQL-driver til Python
import psycopg2
# Giver adgang til DictCursor (rækker kan læses som dictionaries)
import psycopg2.extras


# Connection string til databasen
# host        → hvor databasen kører
# port        → PostgreSQL standardport
# dbname      → navnet på databasen
# user        → database-bruger
# Der findes password, bruges til at logge på db. STÅR HER IKKE
DB_DSN = "host=localhost port=5432 dbname=iot_apotek user=postgres"

# Opretter og returnerer en ny database-forbindelse
def get_conn():
    return psycopg2.connect(DB_DSN)

# Indsætter en ny temperaturmåling i databasen
def insert_measurement(sensor_id, ts, temperatur, location, alarm_flag):

    # Opretter forbindelse (lukkes automatisk pga. with)
    with get_conn() as conn:

        # Opretter cursor til at køre SQL-kommandoer
        with conn.cursor() as cur:

            # SQL INSERT – %s bruges for at undgå SQL injection
            cur.execute(
                """
                INSERT INTO measurements (sensor_id, temperatur, location, alarm_flag)
                VALUES (%s, %s, %s, %s)
                """,
                # Værdierne der indsættes i SQL'en
                (sensor_id, temperatur, location, alarm_flag),
            )

        # Gemmer ændringerne i databasen
        conn.commit()

# Henter den seneste måling for hver sensor
def get_latest_measurements():

    # Opretter databaseforbindelse
    with get_conn() as conn:

        # DictCursor gør at rækker returneres som dictionaries
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:

            # DISTINCT ON bruges til kun at få én række pr. sensor
            # ORDER BY sikrer at den nyeste måling vælges
            cur.execute(
                """
                SELECT DISTINCT ON (sensor_id)
                       sensor_id, timestamp, temperatur, location, alarm_flag
                FROM measurements
                ORDER BY sensor_id, timestamp DESC
                """
            )

            # Konverterer hver række til almindelig dict og returnerer liste
            return [dict(row) for row in cur.fetchall()]

# Henter alle målinger for én specifik sensor
def get_history_for_sensor(sensor_id):

    # Opretter databaseforbindelse
    with get_conn() as conn:

        # Cursor der returnerer rækker som dictionaries
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:

            # SQL SELECT med parameter for sensor_id
            cur.execute(
                """
                SELECT timestamp, temperatur, alarm_flag
                FROM measurements
                WHERE sensor_id = %s
                ORDER BY timestamp
                """,
                # Parameter sendes separat for sikkerhed
                (sensor_id,),
            )

            # Returnerer alle rækker som liste af dictionaries
            return [dict(row) for row in cur.fetchall()]
