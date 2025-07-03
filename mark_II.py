import machine
import time
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED
from join_network import wifi_login
from set_time_by_ntp import set_time

bme = BreakoutBME69X(machine.I2C(), 0x76)
# If this gives an error, try the alternative address
# bme = BreakoutBME69X(machine.I2C(), 0x77)

# Set up our display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
display.set_backlight(0.8)

BLACK = display.create_pen(0, 0, 0)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
AMBER = display.create_pen(255, 191, 0)
BLUE = display.create_pen(0, 0, 255)
WHITE = display.create_pen(255, 255, 255)
PURPLE = display.create_pen(255, 0, 255)

WIDTH, HEIGHT = display.get_bounds()

led = RGBLED(26, 27, 28)

class Display(object):
    def __init__(self, title="Temp & Pressure"):
        self.shadow_offset = 2

        self.title = title
        self.title_font_size = 6
        self.text_font_size = 4
        self.title_lines = []

        remainder = self.title
        while remainder != "":
            line, remainder = self.wrap_text(remainder, WIDTH)
            self.title_lines.append(line)
        print(f"have ended up with {self.title_lines}")
        
    def wrap_text(self, text, width=WIDTH):
        length = display.measure_text(text, self.title_font_size)
        words = text.split()
        drop = 0
        line = text
        remainder = ""
        while length > width :
            drop -= 1
            line = " ".join(words[0:drop])
            remainder = " ".join(words[drop:])
            length = display.measure_text(line, self.title_font_size)
            print(f"text = {" ".join(words[0:drop])} ## length = {length}")
            if length == 0:
                return text, ""
        return line, remainder
#         return text, ""
        
    def draw_title(self):
        letter_height = 8 * self.title_font_size
        vert_space = 10
        for line in self.title_lines:
            length = display.measure_text(line, self.title_font_size)
            #print(f"length is {length}, WIDTH is {WIDTH}")
            # draw 'shadow' first.
            display.set_pen(WHITE)        
            display.text(line, WIDTH // 2 - length // 2 + self.shadow_offset, vert_space + self.shadow_offset, WIDTH, self.title_font_size)
            # draw 'text' on top.
            display.set_pen(BLUE)
            display.text(line, WIDTH // 2 - length // 2, vert_space, WIDTH, self.title_font_size)
            vert_space += letter_height

    def draw_in_box(self, text, loc=0, colour=PURPLE):
        length = display.measure_text(text, self.text_font_size)
        baseline  = 10+2*8*self.title_font_size + 20
#         print(f"baseline is  {baseline}")
        x_offset =  loc%2 * (WIDTH // 2)
        if loc ==4 :
            x_offset = WIDTH // 4
        elif loc ==5 :
            x_offest = 10
        y_offset = baseline + ((loc//2) * 8 * self.text_font_size)
#         print(f"x and y offsets are {x_offset} and {y_offset}")
        display.set_pen(colour)
        display.text(text, (WIDTH // 4) - (length // 2) + x_offset, y_offset, WIDTH, self.text_font_size)
        
    # Helps to keep our main draw function tidy!
    def draw_screen(self):
        display.set_pen(BLACK)
        display.clear()
        self.draw_title()


def average_readings(device):
    repeat = 10.0
    heater_status = []
    tot_temp = 0
    tot_press =0
    tot_humid = 0
    tot_gas = 0
    temp2 = data_buffer(max_len=int(repeat))
    for _ in range(int(repeat)):
        temperature, pressure, humidity, gas, status, _, _ = device.read()
        heater = "Stable" if status & STATUS_HEATER_STABLE else "Unstable"
        heater_status.append(heater)
        temp2.add(temperature)
        
        tot_temp   += temperature
        tot_press  += pressure
        tot_humid  += humidity
        tot_gas    += gas

        time.sleep(6)
    
    temperature = tot_temp  / repeat
    pressure    = tot_press / repeat
    humidity    = tot_humid / repeat
    gas         = tot_gas   / repeat
    heater = "Stable"
    if "Unstable" in heater_status:
        heater = "Unstable"
    
    return temperature, pressure, humidity, gas, heater, temp2.average()

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


log_file = open("bme690_data_II.csv","a")

screens = []
screens.append(Display("Temp & Pressure 2"))
screens.append(Display("Test & Press 2"))

boot_screen = Display("Preparing")
boot_screen.draw_screen()
boot_screen.draw_in_box(f"Wifi", loc=4, colour=RED)
display.update()
wifi_login()
boot_screen.draw_in_box(f"Wifi", loc=4, colour=GREEN)
display.update()
time.sleep(2)

boot_screen.draw_screen()
boot_screen.draw_in_box(f"Time", loc=4, colour=RED)
display.update()
set_time()
boot_screen.draw_in_box(f"Time", loc=4, colour=GREEN)
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
sleep_time = 1
screen_update = 60
log_update = 600
count_reset = screen_update * log_update

readings = bme.read()
temperature.add(readings[0])
pressure.add(readings[1])
humidity.add(readings[2])
gas.add(readings[3])
status = readings[4]
heater.add("Stable" if status & STATUS_HEATER_STABLE else "Unstable")

date = time.localtime()
date_string = f"{date[0]:0>4}/{date[1]:0>2}/{date[2]:0>2}, {date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}"

# The bit the updates the display and sleeps..
while True:
#for thing in range(1):
    count += 1
    count = count % count_reset
    #print(f"Count is {count}")

    if count % screen_update == 0:
        current_screen = ((current_screen + 1) % 2) # 2 should be max_screens
        print(f"current screen is {current_screen}")
        print(f"at {date_string} teperature = {temperature.average()}, humidity = {humidity.average()}"
              f", heater is {"Unstable" if heater.any_match("Unstable") else "Stable"}")

    readings = bme.read()
    temperature.add(readings[0])
    pressure.add(readings[1])
    humidity.add(readings[2])
    gas.add(readings[3])
    status = readings[4]
    heater.add("Stable" if status & STATUS_HEATER_STABLE else "Unstable")

    date = time.localtime()
    date_string = f"{date[0]:0>4}/{date[1]:0>2}/{date[2]:0>2}, {date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}"
    #print(f"at {date_string} teperature = {temperature.average()}, humidity = {humidity.average()}")

    heater_status = "Unstable" if heater.any_match("Unstable") else "Stable"
#    log_string = f"{date_string}, {temperature.average()}, {pressure.average()}, {humidity.average()}, {gas.average()}, {heater_status}\n"
    #print(f"{log_string}")
#    log_file.write(log_string)
#    log_file.flush()

    if current_screen == 0:
        screens[0].draw_screen()
        if temperature.average() < 17.5:
            colour = BLUE
            led.set_rgb(0, 0, 50)
        elif temperature.average() < 21.0:
            colour = GREEN
            led.set_rgb(0, 40, 0)
        elif temperature.average() < 24.0:
            colour = AMBER
            led.set_rgb(50, 20, 0)
        else :
            led.set_rgb(50, 0, 0)
            colour = RED
        screens[0].draw_in_box(f"{temperature.average():.2f}°c", colour=colour)
        screens[0].draw_in_box(f"{humidity.average():.2f}%", loc=1, colour=GREEN)
        screens[0].draw_in_box(f"{gas.average():.0f}", loc=2)
        screens[0].draw_in_box(f"{heater_status}", loc=3)
        display_pressure = pressure.average() / 100
        screens[0].draw_in_box(f"{display_pressure:.1f} hpa", loc=4)
     
        display.update()

    if current_screen == 1:
        screens[1].draw_screen()
        led.set_rgb(0, 0, 0)
        if temperature.average() < 17.5:
            colour = BLUE
        elif temperature.average() < 21.0:
            colour = GREEN
        elif temperature.average() < 24.0:
            colour = AMBER
        else :
            colour = RED
        screens[1].draw_in_box(f"{temperature.average():.2f}°c", colour=colour)
        screens[1].draw_in_box(f"{humidity.average():.2f}%", loc=1, colour=GREEN)
        patch_height = int(HEIGHT*0.75)
        date = time.localtime()
        display.set_pen(BLACK)
        display.rectangle(0,patch_height, WIDTH, HEIGHT - patch_height )
        screens[1].draw_in_box(f"{date[3]:0>2}:{date[4]:0>2}:{date[5]:0>2}", loc=4)
    time.sleep(1)
    display.update()

