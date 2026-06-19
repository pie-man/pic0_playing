import machine
import time
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED
from join_network import wifi_login
from set_time_by_ntp import set_time
from font_heights import get_font_height

bme = BreakoutBME69X(machine.I2C(), 0x76)
# If this gives an error, try the alternative address
# bme = BreakoutBME69X(machine.I2C(), 0x77)

# Set up our display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
display.set_backlight(0.6)

BLACK   = display.create_pen(0, 0, 0)
WHITE   = display.create_pen(255, 255, 255)
RED     = display.create_pen(255, 0, 0)
GREEN   = display.create_pen(0, 255, 0)
BLUE    = display.create_pen(0, 0, 255)
AMBER   = display.create_pen(255, 191, 0)
PURPLE  = display.create_pen(255, 0, 255)
DAVE    = display.create_pen(0, 141, 200)

WIDTH, HEIGHT = display.get_bounds()

GMT_OFFSET = 3600 #BST

led = RGBLED(26, 27, 28)

class Screen(object):
    """A Screen is an object which holds a collection of 'boxes' along with a default background colour.
       Should it also hold defaults for all the box colours and fonts ? and if so how are they inherited ?
       It has methods to refresh the screen, which clears the whole thing to background colour and then draws
       all the boxes. Plus one to just redraw all the dynamic boxes, i.e. those with data that updates."""
    def __init__(self, title="-=# HAL #=-", background=BLACK):
        self.title = title
        self.background = background
        self.boxes={}

    def add_box(self, name="untitled", new_box=None):
        """A Method to add boxes to a screen. Curently assumed to be stored in a dict, hence 'name'
           However, this may need re-visiting."""
        self.boxes[name] = new_box

    def refresh_screen(self, data_dict):
        """A method to clear the whole screen to 'background colour' and then re-fraw all the boxes this screen holds"""
        #display.set_clip(0, 0, WIDTH, HEIGHT)
        display.remove_clip()
        display.set_pen(self.background)
        display.clear()
        for box_name, box in self.boxes.items() :
            box.draw_in_box(data_dict)
                
    def draw_screen(self, data_dict):
        """A method to redraw all the boxes which are labelled as 'dynamic'"""
        for box_name, box in self.boxes.items() :
            if box.style == "dynamic" :
                box.draw_in_box(data_dict)

    def fit_text_to_box(self, text, font="bitmap8", font_scale=7, width=WIDTH, height=HEIGHT):
        """ The PicoGraphics library will wrap text automaticaly if it's wider
            than the width specified. This version breaks lines before that to
            allow them to be individually aligned centrally."""
        # ToDo : how to do this in intelligent boxes ? Maybe add the ability to split a box, and redefine it's 'border' when a line needs to be wrapped ?
        # ToDO : does the routine need to be able to scale up as well as down ? to fill the box as well as ensure the text fits
        # ToDo : how might it cope with 'dyanmic' text i.e. data values
#       ToDo - everything needs to be rethought as all the things that used to get passed in, are now attributes of the box itself.
        words = text.split()
        breaker = " "
        lines = []
        initial_font_scale = font_scale
        # Try to make sure longest words fits within width
        while any(display.measure_text(x, font_scale) > width for x in words) and font_scale > 0:
            font_scale -= 1
        # If the longest word at the smallest scale for the font couldn't fit,
        # Abandon spltting on spaces and just wrap text at the end of each line
        if font_scale == 0:
            font_scale = initial_font_scale
            words = list(text)
            breaker = ""
        # Break the text into lines that fit within width.
        while len(words) > 0:
            cut = len(words)
            while display.measure_text(breaker.join(words[0:cut]), font_scale) > width :
                cut -= 1
            lines.append(breaker.join(words[0:cut]))
            words = words[cut:]
            print(f"Added {lines[-1]}, left with {words}")
        # Final check - if letter height * number of lines > height given, reduce font size and start again.
        if (get_font_height(font) + 1) * font_scale * len(lines) > height:
            font_scale -= 1
            lines, font_scale = self.wrap_text(text, font=font, font_scale=font_scale, width=width, height=height)
        return lines, font_scale


class Screen_old(object):
    """ToDo : This is the outgoing screen object, need to :
        1 : remove all screens set up with this class (just preparing?)
        2 : Preserve the text wrapping and re-sizing routines - they may come in useful
        3 : Make some kind of 'add shadow' method/decorator for the new 'intelligent' boxes"""
    def __init__(self, title="-=# HAL #=-", title_font = "bitmap8",  font_scale = 7, font_thickness = 3):
        self.title = title
        self.title_font = title_font
        self.title_border = 10
        self.title_font_thickness = font_thickness
        display.set_thickness(font_thickness)
        self.title_lines, font_scale = self.wrap_text(title, width=WIDTH - 2*self.title_border, height=HEIGHT//2 - 2*self.title_border, font_scale=font_scale)
        self.title_font_size = font_scale
        print(f"have ended up with {self.title_lines} @ font scale {font_scale}")
        self.shadow_offset = 2
        self.title_height = (get_font_height(self.title_font) + 1) * font_scale * len(self.title_lines) + 2*self.title_border
        print(f" title height is  {self.title_height}")
        self.text_font_size = 3
        self.boxes={}
        
        self.add_box(name="title", x_start=0, y_start=0, box_width=WIDTH, box_height=self.title_height )
        

    def wrap_text(self, text, font="bitmap8", font_scale=7, width=WIDTH, height=HEIGHT):
        """ The PicoGraphics library will wrap text automaticaly if it's wider
            than the width specified. This version breaks lines before that to
            allow them to be individually aligned centrally."""
        words = text.split()
        breaker = " "
        lines = []
        initial_font_scale = font_scale
        # Try to make sure longest words fits within width
        while any(display.measure_text(x, font_scale) > width for x in words) and font_scale > 0:
            font_scale -= 1
        # If the longest word at the smallest scale for the font couldn't fit,
        # Abandon spltting on spaces and just wrap text at the end of each line
        if font_scale == 0:
            font_scale = initial_font_scale
            words = list(text)
            breaker = ""
        # Break the text into lines that fit within width.
        while len(words) > 0:
            cut = len(words)
            while display.measure_text(breaker.join(words[0:cut]), font_scale) > width :
                cut -= 1
            lines.append(breaker.join(words[0:cut]))
            words = words[cut:]
            print(f"Added {lines[-1]}, left with {words}")
        # Final check - if letter height * number of lines > height given, reduce font size and start again.
        if (get_font_height(font) + 1) * font_scale * len(lines) > height:
            font_scale -= 1
            lines, font_scale = self.wrap_text(text, font=font, font_scale=font_scale, width=width, height=height)
        return lines, font_scale


    def add_box(self, name="untitled",
                x_start=0, y_start=0, box_width=WIDTH, box_height=HEIGHT, mk=1, new_box=None):
        """A Method to add boxes to a screen. Curently assumed to be stored in a dict, hence 'name'
           However, this may need re-visiting."""

        if mk == 1:
            self.boxes[name] = (x_start, y_start, box_width, box_height)
        else:
            self.boxes[name] = new_box

    def draw_in_box_plain(self, font="bitmap8", text="Whasssuuup!!", box_name="untitled", colour=PURPLE, background=BLACK, scale=1):
        length = display.measure_text(text, self.text_font_size * scale, fixed_width=True)
        x_start, y_start, box_width, box_height = self.boxes[box_name]
        working_width = box_width - 2* self.title_border
        display.set_clip(x_start, y_start, box_width, box_height)
        display.set_pen(background)
        display.clear()
        x_offset =  x_start + max(((working_width - length) // 2), 0) + self.title_border
        y_offset =  y_start + self.title_border
        display.set_pen(colour)
        display.text(text, x_offset, y_offset, working_width, self.text_font_size * scale, fixed_width=True)
        display.remove_clip
        # ToDo : could boxes call out to word wrap and/or have multiple lines of text e.g. "Temp:\n<temp val>"

    def draw_in_box_with_shadow(self, font="bitmap8", text="OOh Betty!", box_name="untitled", colour=PURPLE, background=BLACK, scale=1):
        ''' A function to draw multi line text, centrally alligned, with a drop shadow'''
        letter_height = (get_font_height(font) + 1) * self.title_font_size
        vert_space = self.title_border
        display.set_font(font)
        x_start, y_start, box_width, box_height = self.boxes[box_name]
        working_width = box_width - 2* self.title_border
        display.set_clip(x_start, y_start, box_width, box_height)
        display.set_pen(background)
        display.clear()
        for line in self.title_lines:
            length = display.measure_text(line, self.title_font_size)
            x_offset = max((WIDTH - length) // 2, self.title_border)
            # draw 'shadow' first.
            display.set_pen(WHITE)        
            display.text(line, x_offset + self.shadow_offset, vert_space + self.shadow_offset,
                         WIDTH - 2 * self.title_border, self.title_font_size)
            # draw 'text' on top.
            display.set_pen(BLUE)
            display.text(line, x_offset, vert_space, WIDTH - 2 * self.title_border, self.title_font_size)
            vert_space += letter_height
            display.remove_clip
        
    # Helps to keep our main draw function tidy!
    def draw_screen(self, data_dict):
        display.set_pen(BLACK)
        display.clear()
        for box_name, box_dims in self.boxes.items() :
            if box_name == "title":
                self.draw_in_box_with_shadow(box_name=box_name, colour=DAVE)
            elif box_name in data_dict.keys():
                self.draw_in_box_plain(box_name=box_name, text=f"{data_dict[box_name]}")
                
class data_box(object):
    """A Class for a 'smart box' which knows where it is on the screen, all about it's font
       and what 'data' it contains. Dynamic boxes hold the name of the key for the value they display.
       'Static' boxes hold the text they display"""
    # ToDo : Add the ability to wrap text, and possibly return the box height on initialisation, or
    #        just top re-size text to get max size in given box dims...
    def __init__(self, box_style="static", box_font = "bitmap8",  font_size = 7,
                 text_colour=PURPLE, box_background=BLACK,
                 box_data="testing", format_string="data : {0}",
                 x_start=0, y_start=0, box_width=WIDTH, box_height=HEIGHT):
        self.style = box_style
        self.box_data = box_data
        self.font = box_font
        if box_font in ["bitmap6", "bitmap8", "bitmap_outline14"]:
            # ToDo : Rethink this to allow for multiple sizes of vector font (which don't have to be integer scaled)
            self.font_scale = font_size
            self.font_thickness = 1
            self.base_shift = 0
        else:
            self.font_thickness = font_size # Assuming vector fonts are scale = 1
            self.font_scale =1              # as they seem too big for the screen otherwise
            self.base_shift = 10 * self.font_scale
        self.text_pen = text_colour
        self.background_pen = box_background
        self.x_start = x_start
        self.y_start = y_start
        self.box_width = box_width
        self.box_height = box_height
        self.border = 10
        self.format_string = format_string
    
    def draw_in_box(self, data_dict):
        if self.style == "static":
            #print(f"Drawing Static box {self.box_data}")
            text = self.format_string.format(self.box_data)
        else :
            #print(f"Drawing Dynamic box {self.box_data}")
            text = self.format_string.format(data_dict[self.box_data])
        display.set_font(self.font)
        length = display.measure_text(text, self.font_scale)
        working_width = self.box_width - 2* self.border
        display.set_clip(self.x_start, self.y_start, self.box_width, self.box_height)
        display.set_pen(self.background_pen)
        display.clear()
        x_offset =  self.x_start + max(((working_width - length) // 2), 0) + self.border
        y_offset =  self.y_start + self.border + self.base_shift
        display.set_pen(self.text_pen)
        display.set_thickness(self.font_thickness)
        display.text(text, x_offset, y_offset, working_width, self.font_scale, )
        display.remove_clip



class data_buffer(object):
    def __init__(self, max_len=10, default_value=0, prefill=False):
        self.max_len = max_len
        self.default_value = default_value
        self.prefill = prefill
        
        if prefill:
            self.data = [default_value for i in range(max_len)]
        else:
            self.data = []
            
    def add(self, value):
        self.data.append(value)
        if len(self.data) > self.max_len:
            self.data = self.data[1:]
    
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

def take_readings_bme(temperature, pressure, humidity, gas, heater):
    readings = bme.read()
    temperature.add(readings[0])
    pressure.add(readings[1])
    humidity.add(readings[2])
    gas.add(readings[3])
    status = readings[4]
    heater.add("Stable" if status & STATUS_HEATER_STABLE else "Unstable")
    return 

def temp_colours(temp):
    if temp < 17.0:
        colour = BLUE
        led_colour = (0, 0, 30)
    elif temp < 18.0:
        colour = AMBER
        led_colour = (25, 10, 0)
    elif temp < 21.0:
        colour = GREEN
        led_colour = (0, 20, 0)
    elif temp < 24.0:
        colour = AMBER
        led_colour = (25, 10, 0)
    else :
        led._colour = (30, 0, 0)
        colour = RED
    return colour, led_colour
    
log_file = open("bme690_data_IV.csv","a")

screens = []
screens.append(Screen("Box Testing 'n' Playing"))
random_box = data_box(box_style="static", box_font = "gothic",  font_size = 2,
                      text_colour=WHITE, box_background=DAVE,
                      box_data="Box Testing 'n' Playing", format_string="{0}",
                      x_start=0, y_start=0, box_width=WIDTH, box_height=130)
screens[-1].add_box("title", new_box=random_box)
random_box = data_box(box_style="static",box_font = "bitmap8",  font_size = 5,
                      text_colour=BLUE, box_background=WHITE,
                      box_data="Temperature", format_string="{0}",
                      x_start=0, y_start=130, box_width=WIDTH, box_height=50)
screens[-1].add_box("parameter_name", new_box=random_box)
random_box = data_box(box_style="dynamic",box_font = "gothic",  font_size = 2,
                      text_colour=PURPLE, box_background=BLACK,
                      box_data="temperature", format_string="{0:.1f}°C",
                      x_start=0, y_start=180, box_width=WIDTH, box_height=60)
screens[-1].add_box("parameter_readout", new_box=random_box)


new_screen = Screen("Max/Min Temp")
new_box = data_box(box_style="static",box_font = "gothic",  font_size = 3,
                      text_colour=PURPLE, box_background=DAVE,
                      box_data="Temperature", format_string="{0}",
                      x_start=0, y_start=0, box_width=WIDTH, box_height=60)
new_screen.add_box("title", new_box=new_box)

new_box = data_box(box_style="dynamic",box_font = "bitmap8",  font_size = 3,
                      text_colour=GREEN, box_background=BLACK,
                      box_data="temperature", format_string="{0:.1f}°C",
                      x_start=0, y_start=60, box_width=WIDTH, box_height=40)
new_screen.add_box("current_t", new_box=new_box)

new_box = data_box(box_style="static",box_font = "bitmap8",  font_size = 5,
                      text_colour=BLUE, box_background=WHITE,
                      box_data="Max :", format_string="{0}",
                      x_start=0, y_start=100, box_width=160, box_height=50)
new_screen.add_box("name_max_t", new_box=new_box)

new_box = data_box(box_style="static",box_font = "bitmap8",  font_size = 5,
                      text_colour=BLUE, box_background=WHITE,
                      box_data="Min :", format_string="{0}",
                      x_start=160, y_start=100, box_width=160, box_height=50)
new_screen.add_box("name_min_t", new_box=new_box)

new_box = data_box(box_style="dynamic",box_font = "gothic",  font_size = 2,
                      text_colour=WHITE, box_background=DAVE,
                      box_data="max_temp", format_string="{0:.1f}°C",
                      x_start=0, y_start=150, box_width=160, box_height=50)
new_screen.add_box("max_t", new_box=new_box)

new_box = data_box(box_style="dynamic",box_font = "gothic",  font_size = 2,
                      text_colour=BLUE, box_background=DAVE,
                      box_data="min_temp", format_string="{0:.1f}°C",
                      x_start=160, y_start=150, box_width=160, box_height=50)
new_screen.add_box("min_t", new_box=new_box)

screens.append(new_screen)
# screens.append(Screen("screen 3"))

boot_screen = Screen_old("Preparing")
boot_screen.add_box("function", x_start=0, y_start=100, box_width=WIDTH, box_height=70)
boot_screen.add_box("status", x_start=0, y_start=170, box_width=WIDTH, box_height=70)
thingy = {}
thingy["function"] = "WiFi"
thingy["status"] = "Seeking"
boot_screen.draw_screen(thingy)
display.update()
wifi_login()
thingy["status"] = "Connected"
boot_screen.draw_screen(thingy)
display.update()
time.sleep(2)

thingy["function"] = "Time"
thingy["status"] = "Connecting"
boot_screen.draw_screen(thingy)
display.update()
set_time()
thingy["status"] = "Updated"
boot_screen.draw_screen(thingy)
display.update()
time.sleep(2)


print(time.localtime())

temperature = data_buffer(max_len=120)
pressure    = data_buffer(max_len=120)
humidity    = data_buffer(max_len=120)
gas         = data_buffer(max_len=120)
heater      = data_buffer(max_len=120)

current_data = {}

current_screen = -1
count = -1
# Time between readings
sleep_time = 1
# Number of readings to take before updateing the screen
screen_update = 30
# Number of readings to take between writes to the log
log_update = 300
# This allows 'count' to be reset to 0 at a point where both the above occur
count_reset = screen_update * log_update

take_readings_bme(temperature, pressure, humidity, gas, heater)

date = time.localtime()
date_string = f"{date[0]:0>4}/{date[1]:0>2}/{date[2]:0>2}, {date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}"

max_temp = -100
min_temp = 100
# The bit the updates the display and sleeps..
while True:
#for thing in range(1):
    count += 1
    count = count % count_reset

    take_readings_bme(temperature, pressure, humidity, gas, heater)
    max_temp = max(temperature.average(), max_temp)
    min_temp = min(temperature.average(), min_temp)

# ToDo : make a data class, or repurpose the current one, to have methods like "get_current_data("temperature")"
# where all the data is also stored (sutup with an _init_) which either has a method to read data or is passed to
# take_readings_bme for it to add data.
    current_data["temperature"] = temperature.average()
    current_data["max_temp"] = max_temp
    current_data["min_temp"] = min_temp
    current_data["pressure"] = pressure.average()
    current_data["humidity"] = humidity.average()
    current_data["gas"] = gas.average()
    current_data["heater_status"] = "Unstable" if heater.any_match("Unstable") else "Stable"
    
    date = time.localtime()
    date_string = f"{date[0]:0>4}/{date[1]:0>2}/{date[2]:0>2}, {date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}"
    #print(f"at {date_string} teperature = {temperature.average()}, humidity = {humidity.average()}")

    if count % screen_update == 0:
        current_screen += 1
        current_screen = current_screen % len(screens) # 2 should be max_screens
        print(f"current screen is {current_screen} of {len(screens)}")
        if (screens[current_screen].title == "Box Testing 'n' Playing" or
           screens[current_screen].title == "Max/Min Temp") :
            screens[current_screen].refresh_screen(current_data)
            display.update()

        #print(f"at {date_string} teperature = {temperature.average()}, humidity = {humidity.average()}"
        #      f", heater is {"Unstable" if heater.any_match("Unstable") else "Stable"}")

    if count % log_update == 0:
        heater_status = "Unstable" if heater.any_match("Unstable") else "Stable"
        log_string = f"{date_string}, {temperature.average()}, {pressure.average()}, {humidity.average()}, {gas.average()}, {heater_status}\n"
        print(f"{log_string}")
        log_file.write(log_string)
        log_file.flush()

    screens[current_screen].draw_screen(current_data)

    display.update()
    time.sleep(1)

