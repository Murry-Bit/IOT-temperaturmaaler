import psycopg2
import psycopg2.extras


DB_DSN = "host=localhost port=5432 dbname=iot_apotek user=postgres"


def get_conn():
    return psycopg2.connect(DB_DSN)

def insert_measurement(sensor_id, ts, temperatur, location, alarm_flag):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO measurements (sensor_id, temperatur, location, alarm_flag)
                VALUES (%s, %s, %s, %s)
                """,
                (sensor_id, temperatur, location, alarm_flag),
            )
        conn.commit()

def get_latest_measurements():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (sensor_id)
                       sensor_id, timestamp, temperatur, location, alarm_flag
                FROM measurements
                ORDER BY sensor_id, timestamp DESC
                """
            )
            return [dict(row) for row in cur.fetchall()]

def get_history_for_sensor(sensor_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT timestamp, temperatur, alarm_flag
                FROM measurements
                WHERE sensor_id = %s
                ORDER BY timestamp
                """,
                (sensor_id,),
            )
            return [dict(row) for row in cur.fetchall()]
