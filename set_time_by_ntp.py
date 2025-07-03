import socket
import struct
import time
import machine

NTP_DELTA = 2208988800
host = "pool.ntp.org"

def set_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    got_time  = False
    while not got_time:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
            val = struct.unpack("!I", msg[40:44])[0]
            t = val - NTP_DELTA
            got_time  = True
        except OSError as exc:
            if exc.args[0] == 110: # ETIMEDOUT
                print(f"Got that Timeout error again...")
                time.sleep(2)
                pass
            print(f"exc.args {exc.args}")
        finally:
            s.close()
#    val = struct.unpack("!I", msg[40:44])[0]
#    t = val - NTP_DELTA    
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
