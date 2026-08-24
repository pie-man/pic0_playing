import network
from pimoroni import RGBLED
import time

led = RGBLED(26, 27, 28)

def wifi_activate() -> network.WLAN:
    """Turns on the WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return wlan

def wifi_scan(wlan: network.WLAN) -> set:
    """Scans and returns a list of available network SSIDs"""
    networks = []
    scans = 0
    max_scans = 5
    while not networks and scans < max_scans:
        networks = wlan.scan()
        scans += 1
        # print(f"Scan {scans} of {max_scans}")
    ssids = set()
    for net in networks:
        dave = net[0].decode('utf-8')
        # print(f"SSID is {dave}")
        if dave:
            ssids.add(dave)
    # print(f"Pulled a list of ssids : {ssids}")
    return ssids

def wifi_select(wlan: network.WLAN, known_networks: dict) -> str:
    """Uses a list of stored credentials to select a network from those available."""
    print(f"Known networks are : {known_networks}")
    to_try = set()
    retries = 5
    while len(to_try) == 0 and retries >0:
        to_try = set(known_networks.keys()).intersection(wifi_scan(wlan))
        print(f"tries left = {retries}")
        retries -= 1
    if not to_try:
        print(f"Bugger - no overlap..")
        raise(ValueError("No known networks visible"))
    for ssid in to_try:
        print(f"Looking at \"{ssid}\"")
        if wifi_login(ssid, known_networks[ssid], wlan):
            print(f"Connected to {ssid}")
            break
        else:
            print(f"Failed to connect to \"{ssid}\"")
    else:
        print(f"Well, wibble my wobbleboard...")
        raise(ValueError("Unable to connect to any network"))
    return ssid

def wifi_login(ssid, password, wlan:network.WLAN) -> bool:
    wlan.connect(ssid, password)

    max_tries = 20
    tries = 0
    full = 60
    shift = int(full/(max_tries))
    red_level = 0
    blu_level = shift * (max_tries)

    while tries < max_tries:
        led.set_rgb(red_level, 0, blu_level)
        print(f"{tries} of {max_tries} : wlan.status is : {wlan.status()}")
        print(f"wlan.status is : {wlan.status()}")
        if wlan.status() == network.STAT_GOT_IP:
            break
        tries += 1
        red_level += shift
        blu_level -= shift
        time.sleep(1)

    return wlan.status() == network.STAT_GOT_IP

    #     led.set_rgb(75, 0, 0)
    #     time.sleep(3)
    #     raise RuntimeError('network connection failed')
        
    # else:
    #     print('connected')
    #     status = wlan.ifconfig()
    #     print( 'ip = ' + status[0] )
