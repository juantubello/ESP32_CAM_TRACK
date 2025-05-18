from machine import Pin, deepsleep, reset_cause, DEEPSLEEP_RESET
import esp32
import network
import time
import urequests as requests
import camera
from time import sleep


led = Pin(2, Pin.OUT)
led.off()  # Asegurar que esté apagado inicialmente

# Configurar el flash
flash = Pin(4, Pin.OUT)  # Flash en GPIO4 en ESP32-CAM

# Configurar el sensor PIR
pir_pin = Pin(13, mode=Pin.IN)

# WiFi credentials
WIFI_SSID = ""
WIFI_PASSWORD = ""

# API endpoint
UPLOAD_URL = ''

def conectar_wifi(ssid, password, timeout=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a WiFi...')
        wlan.connect(ssid, password)
        t = 0
        while not wlan.isconnected() and t < timeout:
            print('Esperando conexión... segundo', t)
            sleep(1)
            t += 1
    if wlan.isconnected():
        print('Conectado! IP:', wlan.ifconfig()[0])
    else:
        print('Error: No se pudo conectar a WiFi')

def tomar_foto():
    print('Inicializando cámara...')
    try:
        camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
        print('Cámara inicializada correctamente')
    except Exception as e:
        print('Error iniciando cámara:', e)
        return None

    print('Capturando foto...')
    try:
        buf = camera.capture()
        print('Foto capturada. Tamaño:', len(buf), 'bytes')
        print('Apagando flash...')
        flash.off()
        return buf
    except Exception as e:
        print('Error capturando foto:', e)
        return None
    finally:
        camera.deinit()  # IMPORTANTE: liberar la cámara después de usarla

def enviar_foto(buf):
    print('Preparando para enviar la foto...')
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    headers = {
        "Content-Type": "multipart/form-data; boundary=" + boundary
    }
    
    body = (
        '--' + boundary + '\r\n'
        'Content-Disposition: form-data; name="gato"\r\n\r\n'
        'Luna\r\n'
        '--' + boundary + '\r\n'
        'Content-Disposition: form-data; name="image"; filename="foto.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + buf + ('\r\n--' + boundary + '--\r\n').encode('utf-8')

    try:
        response = requests.post(UPLOAD_URL, headers=headers, data=body)
        if response is not None:
            print('Respuesta del servidor:', response.status_code)
            try:
                print('Contenido:', response.text)
            except:
                print('No se pudo leer el contenido de la respuesta')
            response.close()
        else:
            print('Error: No se recibió respuesta del servidor.')
    except Exception as e:
        print('Error al enviar la foto:', e)

# Configurar la causa de wake-up
esp32.wake_on_ext0(pin=pir_pin, level=esp32.WAKEUP_ANY_HIGH)

# Programa principal
try:
    if reset_cause() == DEEPSLEEP_RESET:
        print('¡Despertamos por movimiento!')
        print('Conectando a WiFi...')
        conectar_wifi(WIFI_SSID, WIFI_PASSWORD)
        flash.on()
        sleep(1)  # Dale un segundo de luz
        print('Tomando foto...')
        buf = tomar_foto()

        if buf:
            print('Enviando foto...')
            enviar_foto(buf)

    else:
        print('Inicio normal')
        # Puedes hacer alguna otra inicialización si quieres

except Exception as e:
    print('Error en el programa principal:', e)

finally:
    led.on()  # ENCENDER LED para indicar espera
    print('Esperando 120 segundo antes de dormir...')
    sleep(120)
    led.off()  # Apaga el LED
    print('Entrando en deep sleep...')
    deepsleep()

