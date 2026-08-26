"""
A block/module used to set up the device. Seemed like a good idea...
However, the current 'boilerplate' which does all the network collection and log file reading relies
on :
the 'write_text_in_a_box' function - which is also required by routine screen re-draws
An instance of the diplay, to set pens for and draw in.
All the network stuff for setting the clock from the internet

All in, it's a bit of a mess and this may not be the way to go about fixing it...
"""


"""
Possible ToDo's...
TODO: move the display based stuff out to another module
TODO: make the left and top margins for writing in a box default, but passable args
TODO: create a debugger class.
    It should hold a list of statements to write.
    it could calculate the space each comment takes. either by
        performing line wrapping and counting lines
        adjusting the scale for longer statements and then calculatiing the height required by lines at each scale
        or both of the above - didn't I do something similar before ?
    Thus when updated, it pops 'old' statements such that the list fits on a screen and then re-draws the list
TODO: crrate an instance of above, which is what is returned. Allowing later code to update it when it all goes belly up.
"""

import time
from join_network import wifi_activate, wifi_select, wifi_login
from info import wifi_creds2
from set_time_by_ntp import set_time, is_it_daylight_saving_time, one_am_on_last_sunday_of_the_month

class info_log_message(object):
    def __init__(self, message, font, scale):
        self.message = message
        self.font = font
        self.scale = scale
        self.height_reqd = self.calc_text_height(message, font, scale)

    @classmethod
    def calc_text_height(cls, message, font, scale):
        print(f"Calculating text height from : {message} in {font} @ {scale}")
        return 10

class info_logger(object):
    def __init__(self, background, font, scale, max_len=10, prefill=False):
        self.max_len = max_len
        self.background = background
        self.default_font = font
        self.default_scale = scale
        self.logs = []
        self.prefil = prefill

    def add_log(self, new_message, scale=0, font=None):
        """Add's a new message to the list displayed with an optionally set size/scale.
        A scale of zero allows the routine to automaticvally select the text size"""
        print(f"Adding {new_message} to message list at scale {scale}")
        if font is None:
            font = self.default_font # use the default for this log
        new_log = info_log_message(new_message, font, scale)
        self.logs.append(new_log)
        self.logs = self.logs[0-self.max_len:]
        print(f"This logger now contains {len(self.logs)} messages :")
        for count, log in enumerate(self.logs):
            print(f"{count:02} : \"{log.message}\" in {log.font} @ scale {log.scale}")

    def display_logs(self, duration=3):
        """Displays the most recent logs until the screen is full for an overridable display time."""
        print(f"Displaying logs for {duration} seconds")
        screen_height = 100
        height_used = 0
        logs_to_display = []
        for log in self.logs[::-1]:
            if height_used + log.height_reqd <= screen_height:
                height_used += log.height_reqd
                logs_to_display.append(log)
            else:
                break
        for log in logs_to_display[::-1]:
            print(f"\"{log.message}\" in {log.font} @ scale {log.scale}")

def write_text_in_a_box(display, text, TopLeft, width, height, background, ink, scale=3):
    """Does a 'display' instnace need to be passed into this ?
    It seems less than ideal to use one and it's associated methods from 'global' data.."""
    display.set_font("bitmap8")
    l_margin = 8
    t_margin = 3
    # draws a white background for the text
    display.set_pen(background)
    display.rectangle(TopLeft[0], TopLeft[1], width, height)
    # writes the reading as text in the white rectangle
    display.set_pen(ink)
    display.text(text, TopLeft[0] + l_margin, TopLeft[1] + t_margin, scale=scale)

def old_setup_copy_n_paste(display, machine, BLACK, BLUE):
    # set the time..
    try:
        print("Activating WiFi :")
        top_left = [10, 10]
        write_text_in_a_box(display, "Activating WiFi :", top_left, 310, 30, BLACK, BLUE, 3)
        display.update()
        top_left[1] += 30
        wlan = wifi_activate()
        time.sleep(1)
        print("Getting list of known networks")
        write_text_in_a_box(display, "Getting list of known networks:", top_left, 310, 30, BLACK, BLUE, 2)
        display.update()
        top_left[1] += 20
        known_networks = wifi_creds2()
        time.sleep(1)
        print("Selecting and joining...")
        write_text_in_a_box(display, "Selecting and joining...", top_left, 310, 30, BLACK, BLUE, 2)
        display.update()
        top_left[1] += 20
        ssid = wifi_select(wlan, known_networks)
        time.sleep(1)
        print(f"Joining Network {ssid}.")
        write_text_in_a_box(display, f"Joining Network {ssid}.", top_left, 310, 30, BLACK, BLUE, 2)
        display.update()
        top_left[1] += 20
        wifi_login(ssid, known_networks[ssid], wlan)
        time.sleep(1)
        print("Setting time.")
        write_text_in_a_box(display, "Setting time.", top_left, 310, 30, BLACK, BLUE, 3)
        display.update()
        top_left[1] += 30
        time_val = set_time()
        write_text_in_a_box(display, f"T val = {time_val}", top_left, 310, 30, BLACK, BLUE, 3)
        top_left[1] += 30
        write_text_in_a_box(display, f"BST Start = {one_am_on_last_sunday_of_the_month(3, time_val)}", top_left, 310, 30, BLACK, BLUE, 2)
        top_left[1] += 20
        write_text_in_a_box(display, f"BST End = {one_am_on_last_sunday_of_the_month(10, time_val)}", top_left, 310, 30, BLACK, BLUE, 2)
        display.update()
        print("here's that line")
        time.sleep(10)
        top_left[1] = 10
        if is_it_daylight_saving_time(time_val):
            time_val += 3600
            print("I think it's time to save daylight")
            write_text_in_a_box(display, "Daylight Saving", [10,70], 310, 30, BLACK, BLUE, 3)
        else:
            write_text_in_a_box(display, "Time to give up", [10,70], 310, 30, BLUE, BLACK, 3)
        print("Here's that other line")
        time.sleep(5)
        tm = time.gmtime(time_val)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        time.sleep(1)
    except: # Need better exception handling here, but then network stuff needs that too.
        machine.RTC().datetime((2026, 1, 1, 0, 0, 0, 0, 0))
        print("An error has occurred in Setup")
        write_text_in_a_box(display, "Error in Setup :", top_left, 310, 30, BLACK, BLUE, 3)
        display.update()
        time.sleep(10)
    clock = time.localtime()
    text = f"{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
    print(f"{text}")
    write_text_in_a_box(display, text, top_left, 310, 30, BLACK, BLUE, 3)
    top_left[1] += 30
    text = f"{clock[0]:04}/{clock[1]:02}/{clock[2]:02}"
    print(f"{text}")
    write_text_in_a_box(display, text, top_left, 310, 30, BLACK, BLUE, 3)
    display.update()
    top_left[1] += 30
    time.sleep(10)
