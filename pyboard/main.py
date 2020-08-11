import wifimgr
from time import sleep
import machine

try:
  import usocket as socket
except:
  import socket


wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")
import  startwww
import webrepl
webrepl.start()
