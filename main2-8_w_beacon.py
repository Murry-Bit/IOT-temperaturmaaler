from machine import Pin, I2C, PWM, Timer
from time import sleep_ms
import network
import urequests
import ujson
from bme680 import BME680_I2C
import espnow
import time


SSID = "SSID"
PASSWORD = "PASSWORD"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def connect_wifi():
    if not wlan.isconnected():
        print("Forbinder til WiFi...")
        wlan.connect(SSID, PASSWORD)
        timeout = 0
        while not wlan.isconnected() and timeout < 20:
            sleep_ms(500)
            timeout += 1
    if wlan.isconnected():
        print("WiFi OK →", wlan.ifconfig()[0])
    else:
        print("Ingen WiFi – prøver igen senere")

connect_wifi()


POST_URL = "http://172.20.10.10:5000/api/measurements"


# ---------- ESP-NOW BEACON (KUN TIL EKSAMEN) ----------
esp_now = espnow.ESPNow()
esp_now.active(True)

RX_MAC = b'\xD4\x8A\xFC\x68\x9A\xA0'   # <<< SKIFT TIL MAC PÅ DEN ANDEN ESP
esp_now.add_peer(RX_MAC)

beacon_interval = 1000  # ms
next_beacon = 0
# ----------------------------------------------------


servo = PWM(Pin(12), freq=50, duty=77)

def set_servo(angle):
    duty = int(25 + (angle / 180.0) * 100)
    servo.duty(duty)


i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
sensor = BME680_I2C(i2c=i2c, address=0x77)


led_ok = Pin(13, Pin.OUT)   # Grøn
led_bad = Pin(26, Pin.OUT)  # Rød


alarm_active = False

def alarm_on():
    global alarm_active
    if alarm_active:
        return
    alarm_active = True
    print("ALARM! Vifter luften!")
    led_bad.value(1)
    led_ok.value(0)

def alarm_off():
    global alarm_active
    alarm_active = False
    set_servo(90)
    led_ok.value(1)
    led_bad.value(0)
    print("Alarm stoppet – rolig position")


def send_data():
    if not wlan.isconnected():
        connect_wifi()
        if not wlan.isconnected():
            return

    try:
        payload = {
            "sensor_id": "kolesskab",
            "temperatur": round(sensor.temperature, 2),
            "location": "koeleskab"
        }

        r = urequests.post(
            POST_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        print("Sendt →", r.text[:100])
        r.close()
    except Exception as e:
        print("Send fejl:", e)


set_servo(90)
led_ok.value(1)
print("ESP32 Vin-/Medicin-alarm klar!")


def main_loop(timer):
    global next_beacon

    temp = sensor.temperature
    print(f"Temp: {temp:5.2f}°C → ", end="")

    if 2.0 <= temp <= 8.0:
        print("GOD")
        alarm_off()
    else:
        print("DÅRLIG!")
        alarm_on()

        for _ in range(6):
            set_servo(10)
            sleep_ms(80)
            set_servo(170)
            sleep_ms(80)
        sleep_ms(200)

    send_data()

    # ----- ESP-NOW BEACON -----
    now = time.ticks_ms()
    if time.ticks_diff(now, next_beacon) >= 0:
        esp_now.send(RX_MAC, b"beacon", True)
        next_beacon = now + beacon_interval
    # ----- MODTAG ACK + PRINT RSSI -----
    host, msg = esp_now.recv(0)
    if msg:
        pt = esp_now.peers_table
        rssi = pt[list(pt.keys())[0]][0]
        print("RSSI (2-8 ESP):", rssi)


Timer(0).init(period=30000, mode=Timer.PERIODIC, callback=main_loop)

