# This example takes the temperature from the Pico's onboard temperature sensor, and displays it on Pico Display Pack.
# It's based on the thermometer example in the "Getting Started with MicroPython on the Raspberry Pi Pico" book.

import machine
import time
import gc
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from breakout_bme280 import BreakoutBME280
# from join_network import wifi_activate, wifi_select, wifi_login
from info import wifi_creds2
from local_config import hardware
# from set_time_by_ntp import set_time, is_it_daylight_saving_time, one_am_on_last_sunday_of_the_month
from logging_to_disc import Log_File
import onewire, ds18x20, binascii

# set up the display and drawing constants
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)

# set the display backlight to 50%
display.set_backlight(0.5)

WIDTH, HEIGHT = display.get_bounds()
y_offset = 30
x_offset = 50
GRAPH_HEIGHT = HEIGHT - y_offset
GRAPH_WIDTH = WIDTH - x_offset

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
BLUE = display.create_pen(100, 100, 200)
MAGENTA = display.create_pen(200, 100, 200)

    
# set up the cpu temperature sensor
sensor_temp = machine.ADC(4)

# hardware is a dictionary read in from local_config.py. The "LED_pins" key must be deined there.
led = RGBLED(*hardware["LED_pins"])

conversion_factor = 3.3 / (65535)  # used for calculating a temperature from the raw sensor reading

try:
    bme69x = BreakoutBME69X(machine.I2C(), 0x76)
    got_bme69x = True
except(RuntimeError): # need to put actual exception if it's not found here..
    got_bme69x = False

try:
    bme280 = BreakoutBME280(machine.I2C(), 0x76)
    got_bme280 = True
except(RuntimeError): # same again
    got_bme280 = False

try:
    ds_pin = machine.Pin(0)
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
    got_ds18t20 = True
    thermometers = ds_sensor.scan()
except(RuntimeError): # same again
    got_ds18t20 = False
    thermometers = []
thermometer_names = {
     "mug" : "28b9fefa050000d4",
     "cup" : "28e81dfb050000d6",
     "air" : "28828beb050000c9",
}

# TEMP_MIN = 10
# TEMP_MAX = 34
bar_width = 2

cpu_temperatures = []
colour_pallette = {
    "RED" : (255, 0 ,0),
    "GREEN" : (0, 255, 0),
    "BLUE" : (0, 0, 255),
    "YELLOW" : (255, 255, 0),
    "CYAN" : (0, 255, 255),
}

temp_limits = [
    (15.0, colour_pallette["BLUE"]),
    (17.0, colour_pallette["CYAN"]),
    (18.0, colour_pallette["GREEN"]),
    (20.0, colour_pallette["GREEN"]),
    (22.0, colour_pallette["YELLOW"]),
    (24.0, colour_pallette["RED"]),
]
# temp_limits = sorted(temp_limits, key=temp_limits[0])

def free(full=False):
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F + A
    # print(f"Pre  Collect : Ram = {F:6d} bytes free, {A:6d} allocated ({100-F/T*100:02.1f}% used)")
    gc.collect()
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F + A
    # print(f"Post Collect : Ram = {F:6d} bytes free, {A:6d} allocated ({100-F/T*100:02.1f}% used)")

def get_bme_temp():
    if got_bme69x:
        readings = bme69x.read()
        temperature = readings[0]
    elif got_bme280:
        readings = bme280.read()
        # readings[1] anmd readings[2] are pressure and rel. humidity respectively.
        temperature = readings[0]
    else:
        temperature = get_cpu_temp() - 1.75
    return temperature

def get_cpu_temp():
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature

def get_remote_temps(ds18b20_thermometers):
    ds_sensor.convert_temp()
    time.sleep_ms(750)
    temperatures = {}
    for thermometer in ds18b20_thermometers:
        thermometer_id_hex = binascii.hexlify(thermometer)
        thermometer_id = thermometer_id_hex.decode('ascii')
        try:
            temperature = ds_sensor.read_temp(thermometer)
        except:
            temperature = None
        # print(f"Read {thermometer_id} got a reading of {temperature}")
        temperatures[thermometer_id] = temperature
    return temperatures

# def scale_temp(temp, temp_min, temp_max):
#     scale = HEIGHT / (temp_max - temp_min)
#     scaled_temp = (temp - temp_min) * scale
#     return scaled_temp

def temperature_to_color(temp):
    upper_reg = temp_limits[-1][0]
    lower_reg = temp_limits[0][0]
    if temp <= temp_limits[0][0]:
        return temp_limits[0][1]
    elif temp >= temp_limits[-1][0]:
        return temp_limits[-1][1]
    else:
        for i in range(len(temp_limits) -1):
            # print(f"i is {i} : range is {temp_limits[i][0]} <= {temp} < {temp_limits[i+1][0]}")
            if temp >= temp_limits[i][0] and temp < temp_limits[i+1][0]:
                upper_reg = temp_limits[i+1][0]
                lower_reg = temp_limits[i][0]
                upper_colour = temp_limits[i+1][1]
                lower_colour = temp_limits[i][1]
                break

    upper_ratio = float(temp - lower_reg) / float(upper_reg - lower_reg)
    low_ratio = 1.0 - upper_ratio
    colour = [
        int(upper_colour[i] * upper_ratio + lower_colour[i] * low_ratio) for i in range(3)
    ]
    return colour

def plot_line(top_left, data_block, baseline, graph_scale, bar_width):
    prev_t = data_block[0]
    i = 0
    for t in data_block[1:]:
        rect_top, rect_thickness = ( 
            calc_rectangle_coords(t, prev_t, GRAPH_HEIGHT,
                                  baseline, graph_scale)
        )
        colour_shade = calc_rectangle_colour(t, prev_t)
        TEMPERATURE_COLOUR = display.create_pen(*colour_shade)
        display.set_pen(TEMPERATURE_COLOUR)
        display.rectangle(i + top_left[0], rect_top + top_left[1], bar_width, rect_thickness)
        i += bar_width
        prev_t = t

class data_buffer(object):
    def __init__(self, max_len=10, default_value=0.0, prefill=False):
        self.max_len = max_len
        self.default_value = default_value
        if prefill:
            self.data = [default_value for i in range(max_len)]
        else:
            self.data = []
            
    def add(self, value):
        if len(self.data) >= self.max_len:
            # self.data.pop(0)
            self.data = self.data[1:]
        self.data.append(value)
    
    def average(self):
        return sum(self.data) / float(len(self.data))

    def get_max(self):
        return max(self.data)
    
    def get_min(self):
        return min(self.data)

    def any_match(self, value):
        return value in self.data
    
    def get_data(self):
        return self.data

def calc_rectangle_coords(temp, prev_temp, graph_height, baseline, scale=10):
    upper_temp = max(temp, prev_temp) - baseline
    difference = abs(temp - prev_temp)
    top = graph_height - round(upper_temp * scale) - 2
    rect_height = round(difference * scale) + 2
    return top, rect_height

def calc_rectangle_colour(temp, prev_temp):
    mid_temp = min(temp, prev_temp) + abs(temp - prev_temp) / 2.0
    colour_temp = temperature_to_color(mid_temp)
    return colour_temp

def calc_graph_scale(graph_height, max_value, min_value, accuracy=1.0):
    """Given a graph_heigt in pixels along with maximum and minimum values,
    This routine returns the baseline value and a scaling factor to convert
    differences into pixels.
    min_scale, default=2, is the minimum difference from baseline to the top.
    accuracy, default = 1, defines the floor below min_value"""
    # baseline is the 'floor' below 'min' to an accuracy of 'accuracy'
    baseline = (min_value // accuracy ) * accuracy
    topline = ((max_value // accuracy) + 1) * accuracy
    difference = max(accuracy * 2.0, abs(topline - baseline))
    order = 100 / difference
    scale = (graph_height / difference) * order * 10 + 1
    scale = scale // order / 10
    # print(f"min_value = {min_value}, baseline = {baseline}, "
    #       f"max_value = {max_value}, topline = {topline}, "
    #       f"raw scale = {graph_height / abs(topline - baseline)}")
    # print(f"with graph_height {graph_height} and scale {scale}, max temp would be {baseline + (graph_height / scale)}")
    return scale, baseline

def calc_tick_marks(graph_height, graph_scale):
    value_range = graph_height / graph_scale
    # print(f"I think the temp range is {value_range}")
    max_tick_marks = graph_height // 30 # Where tF does (the original value of) 36 come from ? could it be twice text height plus a small margin ?
    # print(f"I think I can squeeze in {max_tick_marks} ticks")
    tick_spacing = max(0.1, value_range / max_tick_marks) # '0.1' ?  posibly 1dp, but WTaF
    tick_spacing = value_range / max_tick_marks # try again, without the 'max' test...
    # print(f"tick marks every {tick_spacing} units")
    upper_limit = int(value_range *10)
    int_tick_spacing = int(tick_spacing * 10)
    # print(f"got upper limit of {upper_limit}, and spacing of {int_tick_spacing}")
    tick_marks = [x/10 for x in range(0, upper_limit, int_tick_spacing)]
    # print(f"gives a set of tick marks : {tick_marks}")
    return tick_marks

def plot_graphs(collection_o_graphable_thingies):
    # TODO: GRAPH_HEIGHT is still global and accuracy is hardwired here...
    # TODO: The concept of TLC (top left corner) is required here to offset where the graph is plotted.
    graph_height = GRAPH_HEIGHT
    scale_to_within = 0.2
    TopLCorner = (0, y_offset)
    plot_window = (TopLCorner[0] + x_offset, TopLCorner[1], WIDTH - y_offset, graph_height)
    # End of TODO block - hopefully
    max_values = []
    min_values = []
    for graphable_thingy in collection_o_graphable_thingies:
        if len(graphable_thingy) == 0:
            return
        max_values.append(max(graphable_thingy))
        # max_values.append(graphable_thingy.get_max())
        # min_values.append(graphable_thingy.get_min())
        min_values.append(min(graphable_thingy))
    max_value = max(max_values)
    min_value = min(min_values)
    graph_scale, baseline = calc_graph_scale(graph_height, max_value, min_value, accuracy=scale_to_within)
    # print(f"MIN value = {min_value},  MAX value = {max_value}, graph_scale = {graph_scale}")
    tick_marks = calc_tick_marks(graph_height, graph_scale)
    # clear the plotting rectangle here...
    # draws a white background for the text
    display.set_pen(BLACK)
    display.rectangle(plot_window[0], plot_window[1], plot_window[2], plot_window[3])
    for tick in tick_marks:
        # Does the '16' below correspond or relate to the 36 changed earlier ? is it something to do with text height ?
        tick_line = round(graph_height + TopLCorner[1] - (tick * graph_scale) - 16)
        tick_val = baseline + tick
        # print(f"going to put {tick_val} @ {tick_line}")
        colour = temperature_to_color(tick_val)
        COLOUR_PEN = display.create_pen(*colour)
        display.set_pen(COLOUR_PEN)
        display.text(f"{tick_val:02.1f}c_", 4, tick_line, scale = 2)
    for graphable_thingy in collection_o_graphable_thingies:
        plot_line(plot_window, graphable_thingy, baseline, graph_scale, bar_width)
        # plot_line(plot_window, graphable_thingy.get_data(), baseline, graph_scale, bar_width)

def write_text_in_a_box(text, TopLeft, width, height, background, ink, scale=3):
    display.set_font("bitmap8")
    l_margin = 8
    t_margin = 3
    # draws a white background for the text
    display.set_pen(background)
    display.rectangle(TopLeft[0], TopLeft[1], width, height)
    # writes the reading as text in the white rectangle
    display.set_pen(ink)
    display.text(text, TopLeft[0] + l_margin, TopLeft[1] + t_margin, scale=scale)

# set the time..
try:
    print("Activating WiFi :")
    top_left = [10, 10]
    write_text_in_a_box("Activating WiFi :", top_left, 310, 30, BLACK, BLUE, 3)
    display.update()
    top_left[1] += 30
    # wlan = wifi_activate()
    time.sleep(1)
    print("Getting list of known networks")
    write_text_in_a_box("Getting list of known networks:", top_left, 310, 30, BLACK, BLUE, 2)
    display.update()
    top_left[1] += 20
    known_networks = wifi_creds2()
    time.sleep(1)
    print("Selecting and joining...")
    write_text_in_a_box("Selecting and joining...", top_left, 310, 30, BLACK, BLUE, 2)
    display.update()
    top_left[1] += 20
    # ssid = wifi_select(wlan, known_networks)
    ssid = "Rhaggy ?"
    time.sleep(1)
    print(f"Joining Network {ssid}.")
    write_text_in_a_box(f"Joining Network {ssid}.", top_left, 310, 30, BLACK, BLUE, 2)
    display.update()
    top_left[1] += 20
    # wifi_login(ssid, known_networks[ssid], wlan)
    time.sleep(1)
    print("Setting time.")
    write_text_in_a_box("Setting time.", top_left, 310, 30, BLACK, BLUE, 3)
    display.update()
    top_left[1] += 30
    # time_val = set_time()
    write_text_in_a_box(f"T val = {time_val}", top_left, 310, 30, BLACK, BLUE, 3)
    top_left[1] += 30
    # write_text_in_a_box(f"BST Start = {one_am_on_last_sunday_of_the_month(3, time_val)}", top_left, 310, 30, BLACK, BLUE, 2)
    top_left[1] += 20
    # write_text_in_a_box(f"BST End = {one_am_on_last_sunday_of_the_month(10, time_val)}", top_left, 310, 30, BLACK, BLUE, 2)
    display.update()
    print("here's that line")
    time.sleep(10)
    top_left[1] = 10
    # if is_it_daylight_saving_time(time_val):
    #     time_val += 3600
    #     print("I think it's time to save daylight")
    #     write_text_in_a_box("Daylight Saving ON", [10,70], 310, 30, BLACK, BLUE, 3)
    # else:
    #     write_text_in_a_box("Daylight Saving OFF", [10,70], 310, 30, BLUE, BLACK, 3)
    print("Here's that other line")
    time.sleep(5)
    # tm = time.gmtime(time_val)
    # machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    machine.RTC().datetime((2026, 1, 1, 0, 0, 0, 0, 0))
    time.sleep(1)
except: # Need better exception handling here, but then network stuff needs that too.
    machine.RTC().datetime((2026, 1, 1, 0, 0, 0, 0, 0))
    print("An error has occurred in Setup")
    write_text_in_a_box("Error in Setup :", top_left, 310, 30, BLACK, BLUE, 3)
    display.update()
    time.sleep(10)
clock = time.localtime()
text = f"{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
# print(f"{text}")
write_text_in_a_box(text, top_left, 310, 30, BLACK, BLUE, 3)
top_left[1] += 30
text = f"{clock[0]:04}/{clock[1]:02}/{clock[2]:02}"
# print(f"{text}")
write_text_in_a_box(text, top_left, 310, 30, BLACK, BLUE, 3)
display.update()
top_left[1] += 30
time.sleep(10)

graph_points = int(GRAPH_WIDTH // bar_width)
graph_ranges = {
    # "24 hours" : {"plot interval" : 720,
    #               "marker scale" : "hours",
    #               "markers" : [0, 6, 12, 18],
    #               "keys" : ["cpu temperature", "pressure", "rel_humidity", "bme temperature"],
    #               "log" : None,
    #               },
    # "A week" : {},
    # "8 hours" : {},
    # "Last hour" : {"plot interval" : 30,
    #               "marker scale" : "mins",
    #               "markers" : [0, 15, 30, 45],
    #               "keys" : ["temperature", "pressure", "rel_humidity"],
    #               "log" : None,
    #               },
    "12 hours" : {"plot interval" : 360,
                  "marker scale" : "hours",
                  "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
                  "keys" : ["mug", "cup", "air"],
                  "log" : None,
                  },
    "Ram Usage" : {"plot interval" : 120,
                  "marker scale" : "mins",
                  "markers" : [0, 15, 30, 45],
                  "keys" : ["PreCollect", "PostCollect"],
                  "log" : None,
                  },
    }

for graph_type in graph_ranges.keys():
    name = f"{graph_type.replace(" ", "_")}.txt"
    # data_len = graph_ranges[graph_type]["plt_interval"] * graph_points
    log_keys = ["timestamp"]
    log_keys.extend(graph_ranges[graph_type]["keys"])
    free()
    new_log = Log_File(name, graph_points, 5, log_keys)
    graph_ranges[graph_type]["log"] = new_log

current_bme_temp = get_bme_temp()
readout_update = 1000 # m seconds

update_count = 0
change_over = 60
current_graph = 0
max_graphs = len(graph_ranges)
list_o_graphs = list(graph_ranges.keys())
all_keys = set()
for graph in list_o_graphs:
    for key in graph_ranges[graph]["keys"]:
        graph_ranges[graph][f"{key}_total"] = 0
        all_keys.add(key)
    graph_ranges[graph]["readings_count"] = 0
    graph_ranges[graph]["last reading"] = time.ticks_ms()

graph_updates = [True for x in range(len(list_o_graphs))]
# Fills the screen with black
display.set_pen(BLACK)
display.clear()

while True:
    tm_at_start = time.ticks_ms()
    # fills the screen with black
    # display.set_pen(BLACK)
    # display.clear()

    current_data = {}
    # Take Sensor readings
    current_bme_temp = get_bme_temp()
    current_cpu_temp = get_cpu_temp()

    remote_temperatures = get_remote_temps(thermometers)

    pre_free_mem = gc.mem_free()
    pre_alloc_mem = gc.mem_alloc()
    total_mem = pre_free_mem + pre_alloc_mem
    # gc.collect()
    free()
    post_free_mem = gc.mem_free()

    for key in all_keys:
        if key == "cpu temperature":
            current_data[key] = current_cpu_temp
        elif key == "bme temperature" or key == "temperature":
            current_data[key] = current_bme_temp
        elif (key == "mug" or key == "cup" or key == "air"):
            current_data[key] = remote_temperatures[thermometer_names[key]]
        elif (key == "PreCollect"):
            current_data[key] = 100 - pre_free_mem / total_mem * 100
        elif (key == "PostCollect"):
            current_data[key] = 100 - post_free_mem / total_mem * 100
        else:
            current_data[key] = None

    for count, graph in enumerate(list_o_graphs):
        changed = False
        for key in current_data.keys():
            if f"{key}_total" in graph_ranges[graph]:
                # print(f"Adding current_data[{key if current_data[key] else "bugger all"}] to {graph}[{key}_total]")
                value = graph_ranges[graph][f"{key}_total"] + current_data[key] if current_data[key] else graph_ranges[graph][f"{key}_total"]
                graph_ranges[graph][f"{key}_total"] = value
                changed = True
        if changed:
            graph_ranges[graph]["readings_count"] += 1
        if time.ticks_diff(time.ticks_ms(), graph_ranges[graph]["last reading"]) >= graph_ranges[graph]["plot interval"] * 1000:
            clock = time.localtime()
            # text = f"{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
            print(f"Adding a new record to {graph} @ {text}")
            # free()
            text = f"{clock[0]:04}/{clock[1]:02}/{clock[2]:02}@{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
            new_record = {}
            new_record["timestamp"] = text
            for key in graph_ranges[graph]["keys"]:
                new_record[key] = graph_ranges[graph][f"{key}_total"] / graph_ranges[graph]["readings_count"]
                graph_ranges[graph][f"{key}_total"] = 0
            graph_ranges[graph]["log"].add_record(new_record)
            graph_ranges[graph]["last reading"] = time.ticks_ms()
            graph_ranges[graph]["readings_count"] = 0
            graph_updates[count] = True
        if count == current_graph and graph_updates[count]:
            title = graph
            if graph == "24 hours":
                plot_graphs([graph_ranges[graph]["log"].get_data("bme temperature"), graph_ranges[graph]["log"].get_data("cpu temperature")])
            elif graph == "12 hours":
                plot_graphs([graph_ranges[graph]["log"].get_data("mug"), graph_ranges[graph]["log"].get_data("cup"), graph_ranges[graph]["log"].get_data("air")])
            elif graph == "Ram Usage":
                plot_graphs([graph_ranges[graph]["log"].get_data("PreCollect"), graph_ranges[graph]["log"].get_data("PostCollect")])
            else:
                plot_graphs([graph_ranges[graph]["log"].get_data("temperature")])
            graph_updates[count] = False
            write_text_in_a_box(title, (100, 0), 100, 26, BLACK, MAGENTA, scale=2)
    # print(f"{graph_updates}")

    update_count += 1
    if update_count >= change_over:
        current_graph += 1
        current_graph = current_graph % max_graphs
        update_count = 0
        # print(f"Changing graph to display \"{list_o_graphs[current_graph]}\"")
        # fills the screen with black
        display.set_pen(BLACK)
        display.clear()
        graph_updates[current_graph] = True


    # heck lets also set the LED to match
    # But cut the brightness to about 5%
    led_colour = [round(val * 0.05) for val in temperature_to_color(current_bme_temp)]
    led.set_rgb(*led_colour)

    text = "{:.2f}".format(current_bme_temp) + "c"
    write_text_in_a_box(text, (0, 0), 100, 26, WHITE, BLACK)

    clock = time.localtime()
    text = f"{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
    write_text_in_a_box(text, (200, 0), 120, 26, BLUE, BLACK)


    # time to update the display
    display.update()

    tm_at_end = time.ticks_ms()
    tm_to_run = time.ticks_diff(tm_at_end, tm_at_start)
    delay = readout_update - tm_to_run
    # print(f"Took {tm_to_run}ms to run, will sleep for {delay}ms")
    time.sleep_ms(delay)
