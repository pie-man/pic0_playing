import network
from join_network import wifi_login
from info import wifi_creds2
from set_time_by_ntp import set_time
import time

print("Hello, I'm about to attempt WiFi access....")
# Initialize the wireless interface in Station mode
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("WiFi is Active :  Scanning.")
# Scan for available Wi-Fi networks
networks = wlan.scan()

print("Scan complete")
# Print each network with its SSID and Signal Strength (RSSI)
for net in networks:
    ssid = net[0].decode('utf-8')  # Decode the SSID bytes to a string
    rssi = net[3]                  # RSSI (Signal strength) in dBm
    print(f"SSID: {ssid} | Signal: {rssi} dBm")

wifi_creds = wifi_creds2()
for net in networks:
    ssid = net[0].decode('utf-8')  # Decode the SSID bytes to a string
    if ssid in wifi_creds:
        wifi_login(ssid, wifi_creds[ssid], wlan)

print("Setting time.")
set_time()
clock = time.localtime()
text = f"{clock[2]:02}/{clock[1]:02}/{clock[0]:02}  {clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
print(f"{text}")
clock = time.gmtime()
text = f"{clock[2]:02}/{clock[1]:02}/{clock[0]:02}  {clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
print(f"{text}")
