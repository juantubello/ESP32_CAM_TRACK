import network
import time
import urequests as requests
import camera
from machine import Pin
from time import sleep

# Configura el flash
flash = Pin(4, Pin.OUT)

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
        return buf
    except Exception as e:
        print('Error capturando foto:', e)
        return None
    finally:
        print('Desinicializando cámara...')
        camera.deinit()

def enviar_foto(buf):
    print('Preparando para enviar la foto...')
    headers = {
        "Content-Type": "image/jpeg"
    }
    try:
        response = requests.post(UPLOAD_URL, headers=headers, data=buf)
        print('Respuesta del servidor:', response.status_code)
        response.close()
    except Exception as e:
        print('Error al enviar la foto:', e)

# Programa principal
try:
    print('Activando flash...')
    flash.value(1)
    sleep(1)  # Dale un segundo para iluminar

    print('Conectando a WiFi...')
    conectar_wifi(WIFI_SSID, WIFI_PASSWORD)

    print('Tomando foto...')
    buf = tomar_foto()

    if buf:
        print('Enviando foto...')
        enviar_foto(buf)
    else:
        print('No se pudo capturar la foto, no se envía nada.')

except Exception as e:
    print('Error general:', e)

finally:
    print('Apagando flash...')
    flash.value(0)