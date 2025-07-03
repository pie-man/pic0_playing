import network
from info import wifi_creds
from pimoroni import RGBLED
import time

led = RGBLED(26, 27, 28)

def wifi_login():
    ssid, password = wifi_creds()

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    max_wait = 11
    red_level = 0
    blu_level = 50

    while max_wait > 0:
        led.set_rgb(0, red_level, blu_level)
        print(f"wlan.status is : {wlan.status()}")
        if wlan.status() < 0 or wlan.status() >= 3:
            print(f"wlan.status is : {wlan.status()}")
            break
        max_wait -= 1
        red_level += 5
        blu_level -= 5
        print('waiting for connection...')
        time.sleep(2)

    if wlan.status() != 3:
        led.set_rgb(0, 75, 0)
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )
