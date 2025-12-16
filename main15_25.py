from machine import Pin, I2C, PWM, Timer
from time import sleep_ms
import network
import urequests
import ujson
from bme680 import BME680_I2C


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


POST_URL = "http://10.245.167.78:5000/api/measurements"  


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
            "sensor_id": "lager",         
            "temperatur": round(sensor.temperature, 2),
            "location": "lager"            
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
    temp = sensor.temperature
    print(f"Temp: {temp:5.2f}°C → ", end="")
   
    if 15.0 <= temp <= 25.0:
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

Timer(0).init(period=30000, mode=Timer.PERIODIC, callback=main_loop)