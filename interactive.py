import machine
import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from logging_to_disc import Log_File
from setup_device import info_logger, info_log_message


display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)
display.set_backlight(0.5)
WIDTH, HEIGHT = display.get_bounds()
print(f"Width of screen is {WIDTH}")

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
BLUE = display.create_pen(100, 100, 200)
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

setup_logs = info_logger(BLACK, "higgedy", 2, 12)

setup_logs.add_log("message 1 is pointless", 3)
setup_logs.add_log("So is message 2 pointless", 2)
setup_logs.add_log("message 3 is also pointless")
setup_logs.add_log("message 5 is completely pointless", 3)
setup_logs.add_log("What happened to message 4 ?", 3)
setup_logs.add_log("Ahhh, there it is", 3)
now = time.localtime()
text = f"{now[0]:04}/{now[1]:02}/{now[2]:02}@{now[3]:02}:{now[4]:02}:{now[5]:02}"
setup_logs.add_log(text, 2, "different font")
setup_logs.add_log("message 8 is pointless", 3)
setup_logs.add_log("message 9 is pointless", 3)
setup_logs.add_log("message 10 is pointless", 3)
now = time.localtime()
text = f"{now[0]:04}/{now[1]:02}/{now[2]:02}@{now[3]:02}:{now[4]:02}:{now[5]:02}"
setup_logs.add_log(text, 3)
setup_logs.display_logs(4)
time.sleep(4)
now = time.localtime()
text = f"{now[0]:04}/{now[1]:02}/{now[2]:02}@{now[3]:02}:{now[4]:02}:{now[5]:02}"
setup_logs.add_log(f"message 10 is {text}", 3)
time.sleep(2.5)
now = time.localtime()
text = f"{now[0]:04}/{now[1]:02}/{now[2]:02}@{now[3]:02}:{now[4]:02}:{now[5]:02}"
setup_logs.add_log(f"message 13 is {text}", 3)
setup_logs.display_logs()
time.sleep(2)

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
