"""Scrappy little routine to allow the user to set the time
Currently only sets time, not date, and only in 24 hour format"""

import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from machine import Pin, RTC

button_a = Pin(12, Pin.IN, Pin.PULL_UP)
button_b = Pin(13, Pin.IN, Pin.PULL_UP)
button_x = Pin(14, Pin.IN, Pin.PULL_UP)
button_y = Pin(15, Pin.IN, Pin.PULL_UP)


class Menu(object):
    def __init__(self, display):
        self.display = display
    # set up constants for drawing
        self.WIDTH, self.HEIGHT = self.display.get_bounds()
        self.BLACK = self.display.create_pen(0, 0, 0)
        self.RED = self.display.create_pen(255, 0, 0)
        self.GREEN = self.display.create_pen(0, 255, 0)
        self.BLUE = self.display.create_pen(0, 0, 255)
        self.WHITE = self.display.create_pen(255, 255, 255)
        self.shadow_offset = 2
        self.cursor = "^^"
        self.setting = True
        self.title = "Please Set the time."

        self.max_parts = 2
        self.digits = [0] * self.max_parts
        self.limits = [24, 60]
        self.current_digit = 0
    # A function to draw only the menu elements.
    # Helps to keep our main draw function tidy!
    def draw_menu(self):
        self.display.set_pen(self.WHITE)
        self.display.clear()

        # Draw the screen title.
        font_scale = 3
        self.display.set_pen(self.BLACK)
        length = self.display.measure_text(self.title, font_scale)
        self.display.text(self.title, self.WIDTH // 2 - length // 2 + self.shadow_offset, 10 + self.shadow_offset, self.WIDTH, font_scale)
        self.display.set_pen(self.BLUE)
        self.display.text(self.title, self.WIDTH // 2 - length // 2, 10, self.WIDTH, font_scale)

        toprow_height = 55
        lowrow_height = 172

        # Label the buttons :
        font_scale = 3
        self.display.set_pen(self.RED)
        self.display.text("+", 8, toprow_height, self.WIDTH, font_scale)
        self.display.set_pen(self.BLACK)
        self.display.text("-", 8, lowrow_height, self.WIDTH, font_scale)
        self.display.set_pen(self.BLUE)
        text = "Next"
        self.display.text(text, self.WIDTH - 8 - self.display.measure_text(text, font_scale), toprow_height, self.WIDTH, font_scale)
        self.display.set_pen(self.GREEN)
        text = "Set"
        self.display.text(text, self.WIDTH - 8 - self.display.measure_text(text, font_scale), lowrow_height, self.WIDTH, font_scale)

        # Display current time.
        for item in range(self.max_parts):
            if item == self.current_digit:
                self.display.set_pen(self.RED)
                self.display.text(self.cursor, 115 + item*60, 130, self.WIDTH, 4)
            else:
                self.display.set_pen(self.BLACK)

            self.display.text(f"{self.digits[item]:02}", 110 + item*60, 100, self.WIDTH, 4)
        self.display.set_pen(self.BLACK)
        self.display.text(":", 160, 100, self.WIDTH, 4)

    def next(self):
        self.current_digit = (self.current_digit + 1) % self.max_parts

    # Do a thing based on the currently selected part of the time
    def user_input(self):

        if button_a.value() == 0: # "+"
            self.digits[self.current_digit] += 1
            self.digits[self.current_digit] = self.digits[self.current_digit] % self.limits[self.current_digit]

        if button_b.value() == 0: # "-"
            self.digits[self.current_digit] -= 1
            self.digits[self.current_digit] = self.digits[self.current_digit] % self.limits[self.current_digit]

        if button_y.value() == 0: # Set
            self.setting = False

        if button_x.value() == 0: # "Next"
            self.next()

def manual_set_time(display):
    menu = Menu(display)

    while menu.setting:
        menu.draw_menu()
        menu.user_input()
        display.update()
        time.sleep(0.1)

    print(f"Will set the time to {menu.digits[0]:02}:{menu.digits[1]:02}")
    RTC().datetime((2026, 1, 1, 0, menu.digits[0], menu.digits[1], 0, 0))

if __name__ == "__main__":
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
    display.set_backlight(0.8)


    manual_set_time(display)
    BLACK = display.create_pen(0, 0, 0)
    BLUE = display.create_pen(0, 0, 255)
    while True:
        display.set_font("bitmap8")
        l_margin = 8
        t_margin = 3
        # draws a white background for the text
        display.set_pen(BLACK)
        display.clear()
        clock = time.localtime()
        text = f"{clock[3]:02}:{clock[4]:02}:{clock[5]:02}"

        display.set_pen(BLUE)
        display.text(text, 100, 100, scale=4)
        display.update()
        time.sleep(1)