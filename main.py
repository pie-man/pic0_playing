# This example takes the temperature from the Pico's onboard temperature sensor, and displays it on Pico Display Pack.
# It's based on the thermometer example in the "Getting Started with MicroPython on the Raspberry Pi Pico" book.

import machine
import time
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE

# set the time..
machine.RTC().datetime((2026, 3, 8, 0, 0, 52, 0, 0))

# set up the display and drawing constants
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)

# set the display backlight to 50%
display.set_backlight(0.5)

WIDTH, HEIGHT = display.get_bounds()
h_offset = 30
w_offset = 50
GRAPH_HEIGHT = HEIGHT - h_offset
GRAPH_WIDTH = WIDTH - w_offset

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
BLUE = display.create_pen(100, 100, 200)

    
# set up the internal temperature sensor
sensor_temp = machine.ADC(4)

# Set up the RGB LED For Display Pack and Display Pack 2.0":
# led = RGBLED(6, 7, 8)

# For Display Pack 2.8" uncomment the following line and comment out the line above:
led = RGBLED(26, 27, 28)

conversion_factor = 3.3 / (65535)  # used for calculating a temperature from the raw sensor reading

bme = BreakoutBME69X(machine.I2C(), 0x76)

TEMP_MIN = 10
TEMP_MAX = 34
bar_width = 2

temperatures = []
cpu_temperatures = []
colour_pallette = {
    "RED" : (255, 0 ,0),
    "GREEN" : (0, 255, 0),
    "BLUE" : (0, 0, 255),
    "YELLOW" : (255, 255, 0),
    "CYAN" : (0, 255, 255),
}

temp_ranges = {
    "too-cold"      : (colour_pallette["BLUE"], 15.0),
    "a-bit-cold"    : (colour_pallette["CYAN"], 17.0),
    "low-comfort"   : (colour_pallette["GREEN"], 18.0),
    "high-comfort"  : (colour_pallette["GREEN"], 20.0),
    "a-bit-hot"     : (colour_pallette["YELLOW"], 22.0),
    "too-hot"       : (colour_pallette["RED"], 24.0),
}
colors = [(0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 255, 0), (255, 0, 0)]

def get_ext_temp():
    readings = bme.read()
    temperature = readings[0]
    return temperature

def get_int_temp():
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature

def scale_temp(temp, temp_min=TEMP_MIN, temp_max=TEMP_MAX):
    scale = HEIGHT / (temp_max - temp_min)
    scaled_temp = (temp - temp_min) * scale
    return scaled_temp

def temperature_to_color(temp):
    temp = min(temp, TEMP_MAX)
    temp = max(temp, TEMP_MIN)

    upper_reg = temp_ranges["too-hot"][1]
    upper_colour = temp_ranges["too-hot"][0]
    lower_reg = temp_ranges["too-cold"][1]
    lower_colour = temp_ranges["too-cold"][0]
    # print(f"temp is {temp}")
    temp_labels = [
        "too-hot", "a-bit-hot", "high-comfort", "low-comfort",
        "a-bit-cold", "too-cold"
    ]
    for comfort_level in temp_labels:
        if temp <= temp_ranges[comfort_level][1]:
            # print(f"setting upper temp range to {comfort_level}")
            upper_reg = temp_ranges[comfort_level][1]
            upper_colour = temp_ranges[comfort_level][0]
    temp_labels.reverse()
    for comfort_level in temp_labels:
        if temp > temp_ranges[comfort_level][1]:
            # print(f"setting lower temp range to {comfort_level}")
            lower_reg = temp_ranges[comfort_level][1]
            lower_colour = temp_ranges[comfort_level][0]
    
    if upper_reg == lower_reg:
        colour = upper_colour
    else:
        upper_ratio = float(temp - lower_reg) / float(upper_reg - lower_reg)
        low_ratio = 1.0 - upper_ratio
        colour = [
            int(upper_colour[i] * upper_ratio + lower_colour[i] * low_ratio) for i in range(3)
        ]
    return colour

def plot_line(data_block, baseline, graph_scale, bar_width):
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
        display.rectangle(i + w_offset, rect_top + h_offset, bar_width, rect_thickness)
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
        self.data.append(value)
        if len(self.data) > self.max_len:
            self.data.pop(0)
    
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

def calc_rectangle_coords(temp, prev_temp, graph_height=GRAPH_HEIGHT, baseline=TEMP_MIN, scale=10):
    upper_temp = max(temp, prev_temp) - baseline
    difference = abs(temp - prev_temp)
    top = graph_height - round(upper_temp * scale) - 2
    rect_height = round(difference * scale) + 2
    return top, rect_height

def calc_rectangle_colour(temp, prev_temp):
    mid_temp = min(temp, prev_temp) + abs(temp - prev_temp) / 2.0
    colour_temp = temperature_to_color(mid_temp)
    return colour_temp

def calc_graph_scale(graph_height, temp_max, temp_min, min_scale=3, accuracy=1.0):
    """Given a graph_heigt in pixels along with maximum and minimum teperaturtes,
    This routine returns the baseline temperature and a scaling factor to convert
    temperature differences into pixels.
    min_scale, default=3, is the minimum difference from baseline to the top in degrees
    accuracy, default = 1, defines the floor below min_temp in degrees"""
    baseline = (temp_min // accuracy ) * accuracy
    difference = max(min_scale, abs(temp_max - baseline))
    scale = ((graph_height / difference) // accuracy ) * accuracy
    print(f"temp_min = {temp_min}, baseline = {baseline}, "
          f"temp_max = {temp_max}, raw scale = {graph_height / abs(temp_max - baseline)}")
    print(f"with graph_height {graph_height} and scale {scale}, max temp would be {(temp_max - baseline) * scale}")
    return scale, baseline

def calc_tick_marks(graph_height, graph_scale):
    temp_range = graph_height / graph_scale
    print(f"I think the temp range is {temp_range}")
    max_tick_marks = graph_height // 36
    print(f"I think I can squeeze in {max_tick_marks} ticks")
    tick_spacing = max(0.1, temp_range / max_tick_marks)
    print(f"tick marks every {tick_spacing} degrees")
    upper_limit = int((GRAPH_HEIGHT // graph_scale) *10)
    int_tick_spacing = int(tick_spacing * 10)
    print(f"got upper limit of {upper_limit}, and spacing of {int_tick_spacing}")
    tick_marks = [x/10 for x in range(0, upper_limit, int_tick_spacing)]
    print(f"gives a set of tick marks : {tick_marks}")
    return tick_marks

def plot_graphs(collection_o_graphable_thingies):
    pass
    max_values = []
    min_values = []
    for graphable_thingy in collection_o_graphable_thingies:
        max_values.append(graphable_thingy.get_max())
        min_values.append(graphable_thingy.get_min())
    max_t = max(max_values)
    min_t = min(min_values)
    graph_scale, baseline = calc_graph_scale(GRAPH_HEIGHT, max_t, min_t, accuracy=0.2)
    print(f"MIN temp = {min_t},  MAX temp = {max_t}, graph_scale = {graph_scale}")
    tick_marks = calc_tick_marks(GRAPH_HEIGHT, graph_scale)
    for tick in tick_marks:
        tick_line = round(GRAPH_HEIGHT + h_offset - (tick * graph_scale) - 18)
        tick_val = baseline + tick
        # print(f"going to put {tick_val} @ {tick_line}")
        colour = temperature_to_color(tick_val)
        COLOUR_PEN = display.create_pen(*colour)
        display.set_pen(COLOUR_PEN)
        display.text(f"{tick_val:02.1f}c", 4, tick_line, scale = 2)
    for graphable_thingy in collection_o_graphable_thingies:
        plot_line(graphable_thingy.get_data(), baseline, graph_scale, bar_width)

current_int_temp = get_int_temp()
current_ext_temp = get_ext_temp()
cpu_temperatures = data_buffer(max_len=GRAPH_WIDTH // bar_width, default_value=current_int_temp, prefill=True)
temperatures = data_buffer(max_len=GRAPH_WIDTH // bar_width, default_value=current_ext_temp, prefill=True)

min_t = min(current_ext_temp, current_int_temp)
max_t = max(current_ext_temp, current_int_temp)
graph_scale, baseline = calc_graph_scale(GRAPH_HEIGHT, max_t, min_t)
print(f"MIN temp = {min_t},  MAX temp = {max_t}, graph_scale = {graph_scale}")
tick_marks = calc_tick_marks(GRAPH_HEIGHT, graph_scale)

graph_update = 1000 # m seconds
readout_update = 500 # m seconds
ref_time = time.ticks_ms()

while True:
    tm_at_start = time.ticks_ms()
    # fills the screen with black
    display.set_pen(BLACK)
    display.clear()

    current_int_temp = get_int_temp()
    current_ext_temp = get_ext_temp()

    # print(f"since ref time it has been {(tm_at_start - ref_time)/1000}s")
    if tm_at_start - ref_time >= graph_update:
        print(f"since ref time it has been {(tm_at_start - ref_time)/1000}s")
        ref_time += graph_update
        cpu_temperatures.add(current_int_temp)
        temperatures.add(current_ext_temp)

    plot_graphs([cpu_temperatures, temperatures])

    # heck lets also set the LED to match
    # But cut the brightness to about 10%
    led_colour = [round(val * 0.1) for val in temperature_to_color(current_ext_temp)]
    led.set_rgb(*led_colour)

    # draws a white background for the text
    display.set_pen(WHITE)
    display.rectangle(1, 0, 100, 26)

    # writes the reading as text in the white rectangle
    display.set_font("bitmap8")
    display.set_pen(BLACK)
    display.text("{:.2f}".format(current_ext_temp) + "c", 8, 3, scale=3)

    # draws a blue background for the text
    display.set_pen(BLUE)
    display.rectangle(200, 0, 120, 26)

    clock = time.localtime()
    # writes the reading as text in the white rectangle
    display.set_pen(BLACK)
    display.text(f"{clock[3]:02}:{clock[4]:02}:{clock[5]:02}", 204, 3, scale=3)

    # time to update the display
    display.update()

    tm_at_end = time.ticks_ms()
    tm_to_run = tm_at_end - tm_at_start
    delay = readout_update - tm_to_run
    # print(f"Took {tm_to_run}ms to run, will sleep for {delay}ms")
    time.sleep_ms(delay)
