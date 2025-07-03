import machine
import time
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import RGBLED
import random


bme = BreakoutBME69X(machine.I2C(), 0x76)
# If this gives an error, try the alternative address
# bme = BreakoutBME69X(machine.I2C(), 0x77)

# Set up our display
#graphics = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)

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

# Constants to play with
NUMBER_OF_STARS = 200
TRAVEL_SPEED = 1.2
STAR_GROWTH = 0.12

class Display(object):
    def __init__(self):
        self.shadow_offset = 2

        self.title = "Temp & Pressure"
        self.title_font_size = 6
        self.text_font_size = 4
        self.title_lines = []

        remainder = self.title
        while remainder != "":
            line, remainder = self.get_line(remainder)
            self.title_lines.append(line)
        print(f"have ended up with {self.title_lines}")

        self.generate_starfield()

        
    def get_line(self, text):
        length = display.measure_text(text, self.title_font_size)
        if length > WIDTH :
            print(f"oops")
            words = text.split()
            print(f"words : {words}")
            drop = 0
            while length > WIDTH :
                drop -= 1
                line = " ".join(words[0:drop])
                remainder = " ".join(words[drop:])
                length = display.measure_text(line, self.title_font_size)
                print(f"text = {" ".join(words[0:drop])} ## length = {length}")
                if length == 0:
                    return text, ""
                return line, remainder

        return text, ""
        

    def draw_title(self):
        letter_height = 8 * self.title_font_size
        vert_space = 10
        for line in self.title_lines:
            length = display.measure_text(line, self.title_font_size)
            # draw 'shadow' first.
            display.set_pen(WHITE)        
            display.text(line, WIDTH // 2 - length // 2 + self.shadow_offset, vert_space + self.shadow_offset, WIDTH, self.title_font_size)
            # draw 'text' on top.
            display.set_pen(BLUE)
            display.text(line, WIDTH // 2 - length // 2, vert_space, WIDTH, self.title_font_size)
            vert_space += letter_height

    def draw_in_box(self, text, loc=0, colour=PURPLE):
        length = length = display.measure_text(text, self.text_font_size)
        baseline  = 10+2*8*self.title_font_size + 20
        #print(f"baseline is  {baseline}")
        x_offset =  loc%2 * (WIDTH // 2)
        if loc ==4 :
            x_offset = WIDTH // 4
        y_offset = baseline + ((loc//2) * 8 * self.text_font_size)
        #print(f"x and y offsets are {x_offset} and {y_offset}")
        display.set_pen(colour)
        display.text(text, (WIDTH // 4) - (length // 2) + x_offset, y_offset, WIDTH, self.text_font_size)
        
    # Helps to keep our main draw function tidy!
    def draw_screen(self):
        display.set_pen(BLACK)
        display.clear()
        #self.draw_starfield()
        self.draw_title()

    def new_star(self):
        # Create a new star, with initial x, y, and size
        # Initial x will fall between -WIDTH / 2 and +WIDTH / 2 and y between -HEIGHT/2 and +HEIGHT/2
        # These are relative values for now, treating (0, 0) as the centre of the screen.
        return [random.randint(0, WIDTH) - WIDTH // 2, random.randint(0, HEIGHT) - HEIGHT // 2, 0.5]

    def generate_starfield(self):
        self.stars = [self.new_star() for _ in range(NUMBER_OF_STARS)]

    def draw_starfield(self):
        display.set_pen(WHITE)
        for i in range(NUMBER_OF_STARS):
            # Load a star from the stars list
            s = self.stars[i]

            # Update x
            s[0] = s[0] * TRAVEL_SPEED

            # Update y
            s[1] = s[1] * TRAVEL_SPEED

            if s[0] <= - WIDTH // 2 or s[0] >= WIDTH // 2 or s[1] <= - HEIGHT // 2 or s[1] >= HEIGHT // 2 or s[2] >= 5:
                # This star has fallen off the screen (or rolled dead centre and grown too big!)
                # Replace it with a new one
                s = self.new_star()

            # Grow the star as it travels outward
            s[2] += STAR_GROWTH

            # Save the updated star to the list
            self.stars[i] = s
            #print(f"s is {s}")

            # Draw star, adding offsets to our relative coordinates to allow for (0, 0) being in the top left corner.
            display.circle(int(s[0]) + WIDTH // 2, int(s[1]) + HEIGHT // 2, int(s[2]))


readout = Display()


# The bit the updates the display and sleeps..
while True:
#for thing in range(1):
    temperature, pressure, humidity, gas, status, _, _ = bme.read()
    heater = "Stable" if status & STATUS_HEATER_STABLE else "Unstable"
    
    readout.draw_screen()
    if temperature < 17.5:
        colour = BLUE
    elif temperature < 21.0:
        colour = GREEN
    elif temperature < 24.0:
        colour = AMBER
    else :
        colour = RED
    readout.draw_in_box(f"{temperature:.2f} c", colour=colour)
    readout.draw_in_box(f"{humidity:.2f}%", loc=1, colour=GREEN)
    readout.draw_in_box(f"{gas:.0f}", loc=2)
    readout.draw_in_box(f"{heater}", loc=3)
    display_pressure = pressure / 100
    readout.draw_in_box(f"{display_pressure:.1f} hpa", loc=4)
 
    display.update()

    time.sleep(10)