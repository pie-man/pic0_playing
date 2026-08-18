import socket
import struct
import time

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
                # print(f"Got that Timeout error again...")
                time.sleep(2)
                pass
            print(f"exc.args {exc.args}")
        finally:
            # print("Reached Finally : Closing socket.")
            s.close()
    return t

def one_am_on_last_sunday_of_the_month(month, time_val):
    # As both March and October have 31 days, we can use the same calculation to determine when the last sunday was
    tm = time.gmtime(time_val)
    for day in range(31,24,-1):
        # print(f"today it is {day} of The Month")
        secs = time.mktime((tm[0], month, day, 1, 0, 0, 0, 0))
        DoW = time.gmtime(secs)[6]
        if DoW == 6:
            # print(f"The {day}th of October is the last Sunday")
            """ Return the seconds from epoch value of 1 am on the last sunday of the month """
            return secs
    else:
        raise(ValueError("Couldn't find last sunday of month"))

def is_it_daylight_saving_time(t):
    # British summer time ends at 01:00 gmt (02:00 BST) on the last sunday in october
    bst_start = one_am_on_last_sunday_of_the_month(3, t)
    bst_end = one_am_on_last_sunday_of_the_month(10, t)
    # print(f"T is {t}")
    # print(f"BST start is {bst_start}")
    # print(f"BST end   is {bst_end}")
    # print(f"Is it daylight saving time is {t>=bst_start and t<bst_end}")
    return t >= bst_start and t < bst_end
