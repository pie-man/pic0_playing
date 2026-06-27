import network
from info import wifi_creds, wifi_creds2
from pimoroni import RGBLED
import time

led = RGBLED(26, 27, 28)

def wifi_activate():
    """Turns on the WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return wlan

def wifi_scan(wlan: network.WLAN):
    """Scans and returns a list of available network SSIDs"""
    networks = wlan.scan()
    ssids = []
    for net in networks:
        dave = net[0].decode('utf-8')
        # print(f"SSID is {dave}")
        ssids.append(dave)
    # print(f"Pulled a list of ssids : {ssids}")
    return ssids

def wifi_select(wlan: network.WLAN, known_networks):
    """Uses a list of stored credentials to select a network from those available."""
    for ssid in wifi_scan(wlan):
        # print(f"Looking at {ssid}")
        if ssid in known_networks:
            return ssid
    else:
        raise(ValueError("Ooops a daisy"))

def wifi_login(ssid, password, wlan:network.WLAN):
    wlan.connect(ssid, password)

    max_wait = 11
    red_level = 0
    blu_level = 50

    while max_wait > 0:
        led.set_rgb(0, red_level, blu_level)
        # print(f"wlan.status is : {wlan.status()}")
        if wlan.status() < 0 or wlan.status() >= 3:
            # print(f"wlan.status is : {wlan.status()}")
            break
        max_wait -= 1
        red_level += 5
        blu_level -= 5
        # print('waiting for connection...')
        time.sleep(2)

    if wlan.status() != 3:
        led.set_rgb(75, 0, 0)
        time.sleep(3)
        raise RuntimeError('network connection failed')
        
    # else:
    #     print('connected')
    #     status = wlan.ifconfig()
    #     print( 'ip = ' + status[0] )
