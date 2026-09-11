# This example takes the temperature from the Pico's onboard temperature sensor, and displays it on Pico Display Pack.
# It's based on the thermometer example in the "Getting Started with MicroPython on the Raspberry Pi Pico" book.

import machine
import time
import gc
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from breakout_bme280 import BreakoutBME280
from info import wifi_creds2
from logging_to_disc import Log_File
import onewire, ds18x20, binascii
from four_buttons import manual_set_time

from local_config import hardware, one_wire_sensor, log_files, graph_ranges

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

got_ds18t20 = False
try:
    ds_pin = machine.Pin(0)
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
    thermometers = ds_sensor.scan()
    if len(thermometers) > 0:
        print(f"Found {len(thermometers)} ds18b20 Thermometers")
        got_ds18t20 = True
except(RuntimeError): # same again
    got_ds18t20 = False
    thermometers = []
    print(f"Error checking for One Wire Thermometers : setting got_ds18t20 to {got_ds18t20}")
thermometers_by_ID = {}
for key, value in one_wire_sensor.items():
    thermometers_by_ID[value] = key

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

def free():
    gc.collect()

def get_bme_temp():
    if got_bme69x:
        readings = bme69x.read()
        temperature = readings[0]
    elif got_bme280:
        readings = bme280.read()
        # readings[1] anmd readings[2] are pressure and rel. humidity respectively.
        temperature = readings[0]
    else:
        temperature = None
    return temperature

def get_cpu_temp():
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature

def get_remote_temps(ds18b20_thermometers):
    temperatures = {}
    if got_ds18t20:
        try:
            ds_sensor.convert_temp()
            time.sleep_ms(750)
        except(KeyboardInterrupt):
            raise
        except:
            print(f"Got an Error in OneWire Lib...")
        for thermometer in ds18b20_thermometers:
            thermometer_id_hex = binascii.hexlify(thermometer)
            thermometer_id = thermometer_id_hex.decode('ascii')
            try:
                temperature = ds_sensor.read_temp(thermometer)
            except:
                temperature = None
                print(f"Something awry reading thermometer : ")
                print(f"Thermometer ID is {thermometer_id} ")
                print(f"Was trying to look at {thermometers_by_ID[thermometer_id]}")
            # print(f"Read {thermometer_id} \"{thermometers_by_ID[thermometer_id]}\" got a reading of {temperature}")
            temperatures[thermometer_id] = temperature
    return temperatures

def get_default_temp(bme_temp, cpu_temp, one_wire_readings,
                     one_wire_IDs, got_bme280, got_bme69x, got_ds18t20):
    default_temp = None
    if got_bme280 or got_bme69x:
        default_temp = bme_temp
    elif got_ds18t20:
        default_temp = one_wire_readings[one_wire_IDs["default"]]
    else:
        default_temp = cpu_temp - 2.5
    return default_temp

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
    first_guess = 0
    prev_t = data_block[first_guess]
    while prev_t is None and first_guess < len(data_block) -1:
        first_guess += 1
        # print(f"looking at ppint {first_guess} in a list of {len(data_block)}")
        prev_t = data_block[first_guess]
    if prev_t is None:
        return
    i = 0
    for t in data_block[-135:]: # Needs to know how wide graph is - replace 135
        if t is not None:
            rect_top, rect_thickness = ( 
                calc_rectangle_coords(t, prev_t, GRAPH_HEIGHT,
                                    baseline, graph_scale)
            )
            colour_shade = calc_rectangle_colour(t, prev_t)
            TEMPERATURE_COLOUR = display.create_pen(*colour_shade)
            display.set_pen(TEMPERATURE_COLOUR)
            display.rectangle(i + top_left[0], rect_top + top_left[1], bar_width, rect_thickness)
            prev_t = t
        i += bar_width

class data_buffer(object):
    """Originally conceived as a FIFO list to limit the size of gathered data
    Suspect this is now redundent(ish) as something similar is now done in 
    logging to disc module and no instances of this class are created."""
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
    """Rather clever, if I do say so myself, but ultimately completely redundant
    routine to create a floating rectangle to join the current reading to the previous vertically.
    Display pack has a 'draw a line from A to B which would have been much better to use..."""
    upper_temp = max(temp, prev_temp) - baseline
    difference = abs(temp - prev_temp)
    top = graph_height - round(upper_temp * scale) - 2
    rect_height = round(difference * scale) + 2
    return top, rect_height

def calc_rectangle_colour(temp, prev_temp):
    """Picks the appropriate 'colour' from the midpoint of two values (temperatures)"""
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
    """This appears to work, for most cases - but needs thought...
    It also needs to clear it's background before drawing as if the graph is updated between 'changes' of plot type
    the the new scale draws over the top of the old one and looks really weird."""
    value_range = graph_height / graph_scale
    # print(f"I think the temp range is {value_range}")
    max_tick_marks = graph_height // 30 # Where tF does (the original value of) 36 come from ? could it be twice text height plus a small margin ?
    # print(f"I think I can squeeze in {max_tick_marks} ticks")
    tick_spacing = value_range / max_tick_marks
    upper_limit = int(value_range *10)
    int_tick_spacing = max(1, int(tick_spacing * 10))  # ended up moiving the max here - it IS needed.
    # print(f"got upper limit of {upper_limit}, and spacing of {int_tick_spacing}")
    tick_marks = [x/10 for x in range(0, upper_limit, int_tick_spacing)]
    # print(f"gives a set of tick marks : {tick_marks}")
    return tick_marks

def plot_graphs(collection_o_graphable_thingies):
    """Oooh, too many issues to list here...
    Needs making into a routine where it's given the location of it's TLC, width and height.
    It should handle clearing the axes (of which an X one still needs adding) and the plot area.
    Right now it still accesses a load of global variables, smells like a farmyard and looks like my bedroom."""
    # TODO: GRAPH_HEIGHT is still global and accuracy is hardwired here...
    # TODO: The concept of TLC (top left corner) is required here to offset where the graph is plotted.
    graph_height = GRAPH_HEIGHT
    scale_to_within = 0.2
    TopLCorner = (0, y_offset)
    plot_window = (TopLCorner[0] + x_offset, TopLCorner[1], WIDTH - y_offset, graph_height)
    # End of TODO block - hopefully
    max_values = []
    min_values = []
    max_data_length = -30
    # print(f"Gonna try plotting a graph wi {len(collection_o_graphable_thingies)} things awn it!")
    for graphable_thingy in collection_o_graphable_thingies:
        dave_count = 0
        dave = []
        for x in  graphable_thingy:
            if x is not None:
                dave.append(x)
                dave_count += 1
        # print(f"That yin had {dave_count} bits O useful data. ", end="")
        max_data_length = max(max_data_length, dave_count)
        if len(dave) == 0:
            # print("")
            continue
        max_values.append(max(dave))
        # max_values.append(graphable_thingy.get_max())
        # min_values.append(graphable_thingy.get_min())
        min_values.append(min(dave))
        # print(f"Geein us a Max value O {max(dave)} an a Min value O {min(dave)}")
        # if len(dave) <=10 or min(dave) < 0.009 or max(dave) < 0.009:
        #     print(dave)
    if len(max_values) == 0:
        write_text_in_a_box("No Data Found", (10,50), WIDTH - 20, HEIGHT - 100, BLUE, WHITE, scale=5)
        # print(f"Got nay Max Values to set a scale by. Bailin ooot.")
        return
    if max_data_length < 3:
        write_text_in_a_box("Not Enough Data Found", (10,50), WIDTH - 20, HEIGHT - 100, BLUE, WHITE, scale=5)
        # print(f"Nay got muny Values te plawt. Buggrin Orf Sharpish.")
        return
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
    """Clears a rectangle to the background pen, and then writes some text, offset by margins in said
    rectangle. Curently used to write the temperature, graph title and time in 3 seperate rectangles
    along the top of the screen (amongst other uses)"""
    display.set_font("bitmap8")
    l_margin = 8
    t_margin = 3
    # draws a coloured background for the text
    display.set_pen(background)
    display.rectangle(TopLeft[0], TopLeft[1], width, height)
    # writes the reading as text in the white rectangle
    display.set_pen(ink)
    display.text(text, TopLeft[0] + l_margin, TopLeft[1] + t_margin, width - 8, scale=scale)

def add_to_a_log(log_name, current_data, log_files_dict, force=False):
        current_log = log_files_dict[log_name]
        reading_made = False
        for key in current_data.keys(): # current_data contains ALL keys, current_log ony has some.
            if f"{key}_total" in current_log:
                # print(f"Adding current_data[{key if current_data[key] else "bugger all"}] to {log_name}[{key}_total]")
                current_value = current_log[f"{key}_total"]
                if current_value is not None:
                    current_value = current_value + current_data[key] if current_data[key] is not None else current_value
                elif current_data[key] is not None:
                    current_value = current_data[key]
                current_log[f"{key}_total"] = current_value
                reading_made = True
        if reading_made:
            current_log["readings_count"] += 1
        if time.ticks_diff(time.ticks_ms(), current_log["last reading"]) >= current_log["log interval"] * 1000 or force:
            clock = time.localtime()
            text = f"{clock[0]:04}/{clock[1]:02}/{clock[2]:02}@{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"
            # print(f"Adding a new record to log \"{log_name}\" @ {text}")
            new_record = {}
            new_record["timestamp"] = text
            # print(f"Current log is {current_log["log"].name} : ")
            for key in current_log["keys"]:
                if current_log[f"{key}_total"] is not None:
                    new_record[key] = current_log[f"{key}_total"] / current_log["readings_count"]
                else:
                    new_record[key] = None
                # print(f"{key} : {new_record[key]}", end=" # ")
                current_log[f"{key}_total"] = None
            # print("..done\n")
            current_log["log"].add_record(new_record)
            current_log["last reading"] = time.ticks_ms()
            current_log["readings_count"] = 0
            current_log["changed"] = True
        return log_files_dict

def take_readings(thermometers, one_wire_sensor,
                  got_bme280, got_bme69x,
                  got_ds18t20, all_log_keys):
    current_data = {}
    current_data["time_of_readings"] = time.ticks_ms()

    # Take Sensor readings
    current_bme_temp = get_bme_temp()
    current_cpu_temp = get_cpu_temp()

    remote_temperatures = get_remote_temps(thermometers)

    default_temp = get_default_temp(current_bme_temp, current_cpu_temp,
                                    remote_temperatures, one_wire_sensor,
                                    got_bme280, got_bme69x, got_ds18t20)

    pre_free_mem = gc.mem_free()
    free()
    post_free_mem = gc.mem_free()

    for key in all_log_keys:
        if key == "cpu temperature":
            current_data[key] = current_cpu_temp
        elif key == "bme temperature":
            current_data[key] = current_bme_temp
        elif (key == "PreCollect"):
            current_data[key] = 100 - pre_free_mem / total_mem * 100
        elif (key == "PostCollect"):
            current_data[key] = 100 - post_free_mem / total_mem * 100
        elif (key in one_wire_sensor):
            try:
                current_data[key] = remote_temperatures[one_wire_sensor[key]]
            except(KeyError):
                current_data[key] = None
        else:
            current_data[key] = default_temp
    #     try:
    #         Thing_t_print = f"{current_data[key]:02.2f}" if current_data[key] else f"{current_data[key]}"
    #     except:
    #         print(f"Couldnee turn {current_data[key]} into summat useful")
    #         Thing_t_print = "{current_data[key]}"
    #     print(f"{key} : {Thing_t_print} #", end=" ")
    # print("done")
    return default_temp, current_data

# set the time..
if hardware["WiFi"]:
    try:
        from set_time_by_ntp import set_time, is_it_daylight_saving_time, one_am_on_last_sunday_of_the_month
        from join_network import wifi_activate, wifi_select, wifi_login
        print("Activating WiFi :")
        top_left = [10, 10]
        write_text_in_a_box("Activating WiFi :", top_left, 310, 30, BLACK, BLUE, 3)
        display.update()
        top_left[1] += 30
        wlan = wifi_activate()
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
        ssid = wifi_select(wlan, known_networks)
        time.sleep(1)
        print(f"Joining Network {ssid}.")
        write_text_in_a_box(f"Joining Network {ssid}.", top_left, 310, 30, BLACK, BLUE, 2)
        display.update()
        top_left[1] += 20
        wifi_login(ssid, known_networks[ssid], wlan)
        time.sleep(1)
        print("Setting time.")
        write_text_in_a_box("Setting time.", top_left, 310, 30, BLACK, BLUE, 3)
        display.update()
        top_left[1] += 30
        time_val = set_time()
        write_text_in_a_box(f"T val = {time_val}", top_left, 310, 30, BLACK, BLUE, 3)
        top_left[1] += 30
        write_text_in_a_box(f"BST Start = {one_am_on_last_sunday_of_the_month(3, time_val)}", top_left, 310, 30, BLACK, BLUE, 2)
        top_left[1] += 20
        write_text_in_a_box(f"BST End = {one_am_on_last_sunday_of_the_month(10, time_val)}", top_left, 310, 30, BLACK, BLUE, 2)
        display.update()
        print("here's that line")
        time.sleep(10)
        top_left[1] = 10
        if is_it_daylight_saving_time(time_val):
            time_val += 3600
            print("I think it's time to save daylight")
            write_text_in_a_box("Daylight Saving ON", [10,70], 310, 30, BLACK, BLUE, 3)
        else:
            write_text_in_a_box("Daylight Saving OFF", [10,70], 310, 30, BLUE, BLACK, 3)
        print("Here's that other line")
        time.sleep(5)
        tm = time.gmtime(time_val)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        time.sleep(1)
    except: # Need better exception handling here, but then network stuff needs that too.
        machine.RTC().datetime((2026, 1, 1, 0, 0, 0, 0, 0))
        print("An error has occurred in Setup")
        write_text_in_a_box("Error in Setup :", top_left, 310, 30, BLACK, BLUE, 3)
        display.update()
        time.sleep(10)
else:
    manual_set_time(display)
    top_left = [10, 10]

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

# Calculate total memory on device
free_mem = gc.mem_free()
allocated_mem = gc.mem_alloc()
total_mem = free_mem + allocated_mem
lines = [f"Total memory is ", f"{total_mem}", f"{free_mem} free", f"{allocated_mem} allocated"]
for text in lines:
    print(f"{text}", end=" : ")
    write_text_in_a_box(text, top_left, 310, 30, BLACK, BLUE, 3)
    top_left[1] += 30
display.update()
print("")

time.sleep(5)

# Set up (expand) the dictionary tracking all the log files
list_o_logs = list(log_files.keys())
all_log_keys = set()
for log_name in list_o_logs:
    log_file_name = f"{log_name.replace(" ", "_")}.txt"
    current_log = log_files[log_name]
    log_keys = ["timestamp"]
    log_keys.extend(current_log["keys"])
    max_records = current_log["max records"] if "max records" in current_log else 135
    buffer_size = current_log["buffer size"] if "buffer size" in current_log else 5
    free()
    new_log = Log_File(log_file_name, max_records, buffer_size, log_keys)
    free()
    current_log["log"] = new_log
    current_log["changed"] = False
    for key in current_log["keys"]:
        current_log[f"{key}_total"] = None
        all_log_keys.add(key)
    current_log["readings_count"] = 0
    current_log["last reading"] = time.ticks_ms()

# Take initial readings
default_temp, current_data = take_readings(thermometers, one_wire_sensor,
                                           got_bme280, got_bme69x,
                                           got_ds18t20, all_log_keys)

# Now add those intial readings to all logs (forcibly)
for log_name in list_o_logs:
    log_files = add_to_a_log(log_name, current_data, log_files, force=True)

readout_update = 1000 # m seconds

update_count = 0
change_over = 30
current_graph_no = 0

max_graphs = len(graph_ranges)
list_o_graphs = list(graph_ranges.keys())
all_graph_keys = set()
for graph in list_o_graphs:
    # for key in graph_ranges[graph]["keys"]:
    #     graph_ranges[graph][f"{key}_total"] = 0
    #     all_graph_keys.add(key)
    # graph_ranges[graph]["readings_count"] = 0
    # graph_ranges[graph]["last reading"] = time.ticks_ms()
    graph_ranges[graph]["changed"] = True

# graph_updates = [True for x in range(len(list_o_graphs))]
log_updates = [True for x in range(len(list_o_logs))]
# Fills the screen with black
display.set_pen(BLACK)
display.clear()

print("Launching main loop now:\n")
while True:
    tm_at_start = time.ticks_ms()

    default_temp, current_data = take_readings(thermometers, one_wire_sensor,
                                               got_bme280, got_bme69x,
                                               got_ds18t20, all_log_keys)

    # Update the logs, and write out if required.
    for log in list_o_logs:
        log_files = add_to_a_log(log, current_data, log_files)

    for count, graph in enumerate(list_o_graphs):
        if count == current_graph_no: # and current_graph["changed"]:
            current_graph = graph_ranges[graph]
            logs = current_graph["logs"]
            # print(f"About to check these logs : {logs} for changes...")
            for log in logs:
                if log_files[log]["changed"]:
                    # print(f"I see changed logs for graph {graph}. ..... oh and I see dead people.")
                    current_graph["changed"] = True
                    log_files[log]["changed"] = False
            if not current_graph["changed"]:
                continue
            title = graph
            write_text_in_a_box(title, (100, 0), 100, 26, BLACK, MAGENTA, scale=2)
            data_streams = []
            for log in logs:
                keys_required = set(current_graph["keys"]).intersection(set(log_files[log]["keys"]))
                # print(f"For graph {title}, looking at log {log} with keys {log_files[log]["keys"]} - Picking {keys_required}")
                for key in keys_required:
                    data_streams.append(log_files[log]["log"].get_data(key))
                    free()
                plot_graphs(data_streams)
            current_graph["changed"] = False

    update_count += 1
    if update_count >= change_over:
        current_graph_no += 1
        current_graph_no = current_graph_no % max_graphs
        update_count = 0
        # print(f"Changing graph to display \"{list_o_graphs[current_graph_no]}\"")
        # fills the screen with black
        display.set_pen(BLACK)
        display.clear()
        graph_ranges[list_o_graphs[current_graph_no]]["changed"] = True

    # heck lets also set the LED to match
    # But cut the brightness to about 5%. It really is very bright.
    if default_temp is not None:
        led_colour = [round(val * 0.05) for val in temperature_to_color(default_temp)]
        text = "{:02.2f}".format(default_temp) + "c"
    else:
        led_colour = [0,0,0]
        text = "No Temp"
    led.set_rgb(*led_colour)

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
