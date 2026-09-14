import machine
import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from logging_to_disc import Log_File


display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)
display.set_backlight(0.5)
WIDTH, HEIGHT = display.get_bounds()
print(f"Width of screen is {WIDTH}")

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
BLUE = display.create_pen(100, 100, 200)
RED = display.create_pen(200, 50, 50)
GREEN = display.create_pen(50, 200, 50)
MAGENTA = display.create_pen(200, 100, 200)

try:
    bme = BreakoutBME69X(machine.I2C(), 0x76)
except(RuntimeError):
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)

def get_ext_temp():
    readings = bme.read()
    temperature = readings[0]
    return temperature

def get_int_temp():
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature

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
    display.update()

def new_timestamp():
    now = time.localtime()
    text = f"{now[0]:04}/{now[1]:02}/{now[2]:02}@{now[3]:02}:{now[4]:02}:{now[5]:02}"
    print(f"{text}")
    write_text_in_a_box(text, (0,0), 310, 30, BLACK, BLUE, 3)
    return text

new_timestamp()

log_1 = Log_File("test_file_1", 50, 5, ["timestamp", "temp", "pressure", "pirate value"])
log_2 = Log_File("test_file_2", 20, 1, ["timestamp", "temp", "pirate value"])

pirates = ["Flint", "Vane", "Rackham", "Silver", "Goonsbury"]

for thingy in range(10):
    data_dict = {}
    data_dict["temp"] = get_int_temp()
    data_dict["timestamp"] = new_timestamp()
    pick_a_pirate = pirates[thingy % len(pirates)]
    data_dict["pirate value"] = pick_a_pirate
    if pick_a_pirate == "Flint":
        data_dict["pressure"] = "oodles"
    else:
        if "pressure" in data_dict:
            del data_dict["pressure"]
    log_1.add_record(data_dict)
    log_2.add_record(data_dict)
    log_1.write_data()
    time.sleep(2)

print(f"Log 1 data is :")
for count, record in enumerate(log_1.data):
    stuff_n_nonsence = zip(log_1.keys, record)
    print(f"{count} : ", end=" ")
    for stuff, nonsence in stuff_n_nonsence:
        print(f"{stuff} = {nonsence}", end=" ")
    print("@")

print(f"Log 2 data is :")
for count, record in enumerate(log_2.data):
    stuff_n_nonsence = zip(log_2.keys, record)
    print(f"{count} : ", end=" ")
    for stuff, nonsence in stuff_n_nonsence:
        print(f"{stuff} = {nonsence}", end=" ")
    print("@")

log_2.write_data()

fh = open("12_hours_bme.txt","r")
fh_out = open ("edited.txt","w")
first_line = fh.readline()
fh_out.write(first_line)
for line in fh:
        data_vals = line.rstrip().split(",")
        timestamp = data_vals[0]
        records = data_vals[1:]
        fixed_pressure = float(records[1])/100
        print(f"fixed pressure is {fixed_pressure}")
        data_vals = [timestamp]
        data_vals.extend([records[0], f"{fixed_pressure:04.1f}", records[2]])
        fh_out.write( f"{','.join(data_vals)}\n" )
fh.close()
fh_out.close()

thickness = 5
for shift in range(11):
    h_shift = round((320/12) * shift)
    v_shift = round((240/12) * shift)
    thickness = round(shift / 2.0) + 1
    display.set_pen(BLACK)
    display.clear()
    display.set_clip(h_shift, v_shift, WIDTH - 2* h_shift, HEIGHT - 2* v_shift)
    for count, colour in enumerate(colours):
        border = count*30 + 10
        tl = [border + h_shift, border]
        tr = [WIDTH - border, border + v_shift]
        bl = [border, HEIGHT - (border + v_shift)]
        br = [WIDTH - (border + h_shift), HEIGHT - border]
        display.set_pen(colour)
        display.line(*tl, *tr, thickness)
        display.line(*tr, *br, thickness)
        display.line(*br, *bl, thickness)
        display.line(*bl, *tl, thickness)
        display.update()
        time.sleep(0.5)
    display.remove_clip()


record = ["2026/09/12@03:08:36","18.52251","19.03584","18.50207","18.52547"]
timestring = record[0]
def timestamp_to_seconds(timestamp):
    date, clock = timestamp.split("@")
    yy, mm, dd = date.split("/")
    year = int(yy)
    month = int(mm)
    day = int(dd)
    hh, MM, ss = clock.split(":")
    hour = int(hh)
    min = int(MM)
    sec = int(ss)
    return time.mktime((year, month, day, hour, min, sec, 0, 0))

data_block=[]
with open("/12_hours_ds18b20.txt", "r") as fh:
            print("open..")
            keys_as_text = fh.readline().strip()
            print(f"read keys as : {keys_as_text}")
            file_keys = keys_as_text.split(",")
            data_read = 0
            for line in fh:
                data_vals = line.rstrip().split(",")
                print(f"Data vals point 1 = {data_vals}")
                timestamp = timestamp_to_seconds(data_vals[0]) if data_vals[0] !="no record" else None
                records = [float(x) if x !="no record" else None for x in data_vals[1:]]
                print(f"data_vals[1:] = {data_vals[1:]}")
                print(f"records = {records}")
                data_vals = [timestamp]
                data_vals.extend(records)
                data_block.append(data_vals)


def plot_graph(top_left_x, top_left_y, plot_width, plot_height,
               min_value, value_range, x_start_value, x_range,
               data_block, data_pairs):
    """ Routine to plot a (multi) line graph in a rectangular area of screen.
    Requires the x and y coords of the top left corner, plus the width and height.
    Also requires a minumum value for the x and y scales and the ranges of both values
    It requires a 'data block', a multi dimensional array where each record (line)
    is a list of values (at least 2 if intending to plot anything).
    Finally it requires a list of tuples called "data_pairs" - slightly misnamed as there
    can be an optional third value in the Tuple.
    The first value in the tuple is the column of the data block to use for X coordinates.
    The second value in the tuple is the column of the data block to use for Y coordinates.
    The third, optional, value should be a 'pen' type for the screen and sets the colour of
    the line to draw. If not specified, the line will be the same colour as the previous line.
    If the first tuple doesn't have a third value, the line will be drawn in the same colour
    as the background... doh.
    """
    # Clears the rectangle we're going to plot into with a BLACK background
    display.set_pen(BLACK)
    display.rectangle(top_left_x, top_left_y, plot_width, plot_height)
    display.update()
    # Sets a boundary so all the following plotting functions can only draw within that rectangle.
    # This means values outside of the baselines and ranges won't be seen, but equally won't draw
    # over elements outside the 'plot' window.
    display.set_clip(top_left_x, top_left_y, plot_width, plot_height)
    for plot_pair in data_pairs: # Loops over data pairs to draw each line requested.
        x_column = plot_pair[0]
        y_column = plot_pair[1]
        if len(plot_pair) > 2:
             display.set_pen(plot_pair[2])
        # duration_in_s = data_block[-1][x_column] - data_block[0][x_column]
        pixels_per_unit = plot_width / x_range
        vertical_scale = value_range / plot_height
        # pixels_per_reading = pixels_per_unit * 720 # 12 hours of data, a reading every 6 mins
        previous_y_value = data_block[0][y_column]
        previous_x_value = data_block[0][x_column]
        for readings in data_block[1:]: # skipping the first 'line' as if it's one of log files, it's the keys.
            # maybe that line should be stripped off outside this routine, but I think slices = copies so skipping
            # could be saving memory....
            x_value = readings[x_column]
            x_coord_old = top_left_x + round((previous_x_value - x_start_value) * pixels_per_unit)
            y_coord_old = top_left_y + round(plot_height - ((previous_y_value - min_value) / vertical_scale))
            x_coord_new = top_left_x + round((x_value - x_start_value) * pixels_per_unit)
            y_coord_new = top_left_y + round(plot_height - ((readings[y_column] - min_value ) / vertical_scale))
            # print(f"{readings[y_column]} c at a height of {y_coord_new} pixels")
            display.line(x_coord_old, y_coord_old, x_coord_new, y_coord_new, 2)
            previous_y_value = readings[y_column]
            previous_x_value = x_value
    display.update()
    # time.sleep(0.5)
    display.remove_clip()

display.set_pen(BLACK)
display.clear()
display.set_pen(MAGENTA)
plot_graph(0, 0, WIDTH, HEIGHT,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, [(0,1, WHITE)])
display.set_pen(BLUE)
time.sleep(2)
plot_graph(0, 120, WIDTH, 120,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, [(0,1, BLUE)])
display.set_pen(WHITE)
time.sleep(2)
plot_graph(WIDTH//2, 0, WIDTH//2, HEIGHT,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, [(0,1, RED)])
display.set_pen(WHITE)
time.sleep(2)
plot_graph(WIDTH//4, HEIGHT//4, WIDTH//2, HEIGHT//2,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, [(0,1, WHITE)])
time.sleep(2)

display.set_pen(GREEN)
display.clear()
plotables = [
     (0,1, BLUE),
     (0,2, RED),
     (0,3, MAGENTA),
]
plot_graph(WIDTH//2, HEIGHT//2, WIDTH//2, HEIGHT//2,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, plotables)
plot_graph(0, 0, WIDTH//2, HEIGHT//2,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, plotables)
plot_graph(WIDTH//2, 0, WIDTH//2, HEIGHT//2,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, plotables)
plot_graph(0, HEIGHT//2, WIDTH//2, HEIGHT//2,
           20, 4,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, plotables)
display.set_pen(GREEN)
display.rectangle(WIDTH//4 - 20, HEIGHT//4 -20 , WIDTH//2 + 40, HEIGHT//2 +40)
display.update()
plot_graph(WIDTH//4, HEIGHT//4, WIDTH//2, HEIGHT//2,
           20, 3,
           data_block[0][0], data_block[-1][0] - data_block[0][0],
           data_block, plotables)
