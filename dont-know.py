import machine
import time
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB332
from pimoroni import RGBLED
from join_network import wifi_login
from set_time_by_ntp import set_time

bme = BreakoutBME69X(machine.I2C(), 0x76)
# If this gives an error, try the alternative address
# bme = BreakoutBME69X(machine.I2C(), 0x77)

# Set up our display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB332, rotate=0)
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

display.set_pen(BLACK)
display.clear()
#display.set_pen(PURPLE)        
#display.text("Hello World", 10, 20, WIDTH - 10, 10)
display.update()

boxes = []
boxes.append((0,0, WIDTH // 2, HEIGHT // 2))
display.set_clip(boxes[0][0],boxes[0][1],boxes[0][2], boxes[0][3])
display.set_pen(AMBER)        
display.clear()
display.update()
#display.remove_clip()
display.set_pen(PURPLE)        
display.text("Hello World", 10, 20, WIDTH - 10, 10)
display.update()
