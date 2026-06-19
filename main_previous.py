import machine
import time
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED
from join_network import wifi_activate, wifi_select
from set_time_by_ntp import set_time
from font_heights import get_font_height

bme = BreakoutBME69X(machine.I2C(), 0x76)
# If this gives an error, try the alternative address
# bme = BreakoutBME69X(machine.I2C(), 0x77)

# Set up our display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
display.set_backlight(0.8)

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
    def __init__(self, title="UnTitled", title_font = "bitmap8", font_scale = 7, font_thickness=3):
        # ToDo : Title Font, border (and preffered height?) should be passed in upon creation
        self.title_font = title_font
        self.title_border = 10
        self.title_font_thickness = font_thickness
        display.set_thickness(font_thickness)
        self.title_lines,  font_scale = self.wrap_text(title, title_font ,font_scale, width=WIDTH, height=HEIGHT//2 - 2*self.title_border)
        self.title_font_size = font_scale
        print(f"have ended up with {self.title_lines} @ font scale {font_scale}")
        self.shadow_offset = 2
        self.title_height = (get_font_height(self.title_font) + 1) * font_scale * len(self.title_lines) + 2*self.title_border
        print(f" title height is  {self.title_height}")
        # ToDo : Maybe a way of getting title_height to allow calculation of box heights relative to that ?
        # ToDo : Maybe shift setting font sizes into box creation (and maybe even font too)
        self.text_font_size = 3
        self.boxes = []
        self.boxes_II = {}
        # 1st box, for title, is half the screen
        # ToDo : add a box creating method so the 'screens' can have different boxes
        self.add_box(name="title", background_colour=BLACK, font_colour=BLUE,
                     x_start=0, y_start=0, box_width=WIDTH, box_height=self.title_height )

        self.add_box(name="UnTitled1", background_colour=BLACK, font_colour=BLUE,
                     x_start=0, y_start=self.title_height, box_width=WIDTH // 2, box_height=(HEIGHT - self.title_height) // 2 )

        self.add_box(name="UnTitled2", background_colour=BLACK, font_colour=BLUE,
                     x_start=WIDTH // 2, y_start=self.title_height, box_width=WIDTH // 2, box_height=(HEIGHT - self.title_height) // 2 )
        
        next_start = self.title_height + (HEIGHT - self.title_height) // 2
        self.add_box(name="UnTitled3", background_colour=BLACK, font_colour=BLUE,
                     x_start=0, y_start=next_start, box_width=WIDTH // 2, box_height=(HEIGHT - next_start) )
        
        self.add_box(name="UnTitled4", background_colour=BLACK, font_colour=BLUE,
                     x_start=WIDTH // 2, y_start=next_start, box_width=(WIDTH// 2), box_height=(HEIGHT - next_start) )
        
        self.add_box(name="UnTitled5", background_colour=BLACK, font_colour=BLUE,
                     x_start=0, y_start=next_start, box_width=WIDTH, box_height=(HEIGHT - next_start) )
        
        
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

    def draw_title(self, font="bitmap8"):
        letter_height = (get_font_height(font) + 1) * self.title_font_size
        vert_space = self.title_border
        display.set_font(font)
        for line in self.title_lines:
            length = display.measure_text(line, self.title_font_size)
            x_offset = max((WIDTH - length) // 2, self.title_border)
            #print(f"length is {length}, WIDTH is {WIDTH}")
            # draw 'shadow' first.
            display.set_pen(WHITE)        
            display.text(line, x_offset + self.shadow_offset, vert_space + self.shadow_offset,
                         WIDTH - 2 * self.title_border, self.title_font_size)
            # draw 'text' on top.
            display.set_pen(BLUE)
            display.text(line, x_offset, vert_space, WIDTH - 2 * self.title_border, self.title_font_size)
            vert_space += letter_height
# ToDo : don't think this one is needed any more...
    def mucking_aboot_wee_boxes(self, box_no):
        x_start, y_start, x_finish, y_finish = self.boxes[box_no]
        display.set_clip(x_start, y_start, x_finish, y_finish)
        display.set_pen(DAVE)
        display.clear()
        self.draw_title(font=self.title_font)
        display.remove_clip

    def add_box(self, name="untitled", background_colour=BLACK, font_colour=BLUE,
                x_start=0, y_start=0, box_width=WIDTH, box_height=HEIGHT):
        self.boxes_II[name] = (x_start, y_start, box_width, box_height)
        self.boxes.append((x_start, y_start, box_width, box_height))

    def draw_in_box(self, text, box_no=1, colour=PURPLE, background=BLACK, scale=1):
        length = display.measure_text(text, self.text_font_size * scale)
        x_start, y_start, box_width, box_height = self.boxes[box_no]
        working_width = box_width - 2* self.title_border
        display.set_clip(x_start, y_start, box_width, box_height)
        display.set_pen(background)
        display.clear()
        x_offset =  x_start + self.title_border
        x_offset =  x_start + max(((working_width - length) // 2),0) + self.title_border
        y_offset =  y_start + self.title_border
        display.set_pen(colour)
        display.text(text, x_offset, y_offset, working_width, self.text_font_size * scale)
        display.remove_clip
        # ToDo : could boxes call out to word wrap and/or have multiple lines of text e.g. "Temp:\n<temp val>"
        
    # Helps to keep our main draw function tidy!
    # ToDo : Possibly becoming redundent
    #      - If each screen becomes write title
    #        once and then loop over the boxes to update them as readings are taken
    def draw_screen(self):
        display.set_pen(BLACK)
        display.clear()
        self.mucking_aboot_wee_boxes(0)


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


    def any_match(self, value):
        return value in self.data

def take_readings_bme(temperature, pressure, humidity, gas, heater):
    readings = bme.read()
    temperature.add(readings[0])
    pressure.add(readings[1])
    humidity.add(readings[2])
    gas.add(readings[3])
    status = readings[4]
    heater.add("Stable" if status & STATUS_HEATER_STABLE else "Unstable")
    return 

def quick_title(font="bitmap8", scale=2,lines=("Hello", "World"), font_col=BLUE, shadow_col=BLACK ):
    letter_height = (get_font_height(font) + 1) * scale
    vert_drop = 30
    display.set_font(font)
    shadow_offset = 2
    for line in lines:
        length = display.measure_text(line, scale)
        x_offset = max((WIDTH - length) // 2 , 0)
        print(f"length is {length}, WIDTH is {WIDTH}")
        # draw 'shadow' first.
        display.set_pen(shadow_col)        
        display.text(line, x_offset + shadow_offset, vert_drop + shadow_offset, WIDTH, scale)
        # draw 'text' on top.
        display.set_pen(font_col)
        display.text(line, x_offset, vert_drop, WIDTH, scale)
        vert_drop += letter_height

def temp_colours(temp):
    if temp < 17.5:
        colour = BLUE
        led_colour = (0, 0, 30)
    elif temp < 21.0:
        colour = GREEN
        led_colour = (0, 20, 0)
    elif temp < 24.0:
        colour = AMBER
        led_colour = (25, 10, 0)
    else :
        led_colour = (30, 0, 0)
        colour = RED
    return colour, led_colour
    
log_file = open("bme690_data_II.csv","a")

screens = []
screens.append(Screen("Temperature, Pressure & Humidity"))
screens.append(Screen("Time, Temp & Humidity"))
screens.append(Screen("Temperature"))

boot_screen = Screen("Preparing", title_font="bitmap8", font_scale = 1, font_thickness=3)
boot_screen.draw_screen()
boot_screen.draw_in_box(f"Wifi", box_no=5, colour=RED)
display.update()
# set the time..
try:
    print("Activating WiFi :")
    wlan = wifi_activate()
    print("Getting list of known networks")
    known_networks = wifi_creds2()
    print("Selecting and joining...")
    wifi_select(wlan, known_networks)
except: # Need better exception handling here, but then network stuff needs that too.
    machine.RTC().datetime((2026, 3, 8, 0, 0, 52, 0, 0))
boot_screen.draw_in_box(f"Wifi", box_no=5, colour=GREEN)
display.update()
time.sleep(2)

boot_screen.draw_screen()
boot_screen.draw_in_box(f"Time", box_no=5, colour=RED)
display.update()
set_time()
boot_screen.draw_in_box(f"Time", box_no=5, colour=GREEN)
display.update()
time.sleep(2)

#date = time.localtime()
#date_string = f"{date[0]:0>4}/{date[1]:0>2}/{date[2]:0>2}, {date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}"
#screens[0].draw_screen()
#screens[0].draw_in_box(f"{date_string}", loc=4, colour=GREEN)
#display.update()

print(time.localtime())

temperature = data_buffer(max_len=120)
pressure    = data_buffer(max_len=120)
humidity    = data_buffer(max_len=120)
gas         = data_buffer(max_len=120)
heater      = data_buffer(max_len=120)

current_screen = -1
count = -1
# Time between readings
sleep_time = 1
# Number of readings to take before updateing the screen
screen_update = 60
# Number of readings to take between writes to the log
log_update = 600
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

    if count % screen_update == 0:
        current_screen = ((current_screen + 1) % len(screens))
        #print(f"current screen is {current_screen}")
        #print(f"at {date_string} teperature = {temperature.average()}, humidity = {humidity.average()}"
        #      f", heater is {"Unstable" if heater.any_match("Unstable") else "Stable"}")

    take_readings_bme(temperature, pressure, humidity, gas, heater)

    date = time.localtime()
    date_string = f"{date[0]:0>4}/{date[1]:0>2}/{date[2]:0>2}, {date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}"
    #print(f"at {date_string} teperature = {temperature.average()}, humidity = {humidity.average()}")
    if date[3] == 0 and date[4] ==0 : # It's midnight...
        # Reset the max and min temps to one's which should be immediately overridden
        max_temp = -100
        min_temp = 100
    max_temp = max(temperature.average(), max_temp)
    min_temp = min(temperature.average(), min_temp)

    if count % log_update == 0:
        heater_status = "Unstable" if heater.any_match("Unstable") else "Stable"
        log_string = f"{date_string}, {temperature.average()}, {pressure.average()}, {humidity.average()}, {gas.average()}, {heater_status}\n"
        print(f"{log_string}")
        log_file.write(log_string)
        log_file.flush()

    # ToDo : If 'screens' are in an array - they could be looped over each time we hit 'screen update'
    #      - then only the 'current screen' would need to be drawn here...
    if current_screen == 0:
        screens[0].draw_screen()
        colour, led_colour = temp_colours(temperature.average())
        led.set_rgb(led_colour[0], led_colour[1], led_colour[2])
        screens[0].draw_in_box(f"{temperature.average():.2f}°c", colour=colour)
        screens[0].draw_in_box(f"{humidity.average():.2f}%", box_no=2, colour=GREEN)
        #screens[0].draw_in_box(f"{gas.average():.0f}", loc=2)
        #screens[0].draw_in_box(f"{heater_status}", loc=3)
        display_pressure = pressure.average() / 100
        screens[0].draw_in_box(f"{display_pressure:.1f} hpa", box_no=5, colour=BLUE)
    elif current_screen == 1:
        screens[1].draw_screen()
        led.set_rgb(0, 0, 0)
        colour, led_colour = temp_colours(temperature.average())
        led.set_rgb(led_colour[0], led_colour[1], led_colour[2])
        screens[1].draw_in_box(f"{temperature.average():.2f}°c", box_no=1, colour=colour)
        screens[1].draw_in_box(f"{humidity.average():.2f}%", box_no=2, colour=GREEN)
        date = time.localtime(time.time()+GMT_OFFSET)
        screens[1].draw_in_box(f"{date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}", box_no=5, colour=DAVE, scale=2)
    elif current_screen == 2:
        screens[2].draw_screen()
        led.set_rgb(0, 0, 0)
        colour, led_colour = temp_colours(temperature.average())
        led.set_rgb(led_colour[0], led_colour[1], led_colour[2])
        screens[2].draw_in_box(f"Current :", box_no=1, colour=colour)
        screens[2].draw_in_box(f"{temperature.average():.2f}°c", box_no=2, colour=colour)
        max_colour, _ = temp_colours(max_temp)
        min_colour, _ = temp_colours(min_temp)
        screens[2].draw_in_box(f"Max : {max_temp:.2f}°c", box_no=3, colour=max_colour)
        screens[2].draw_in_box(f"Min : {min_temp:.2f}°c", box_no=4, colour=min_colour)

    time.sleep(1)
    display.update()

