# A config file, not intended to be updated in the repository but to contain
# data specific to the hardware or location the software is run.
# Originally intended to be a TOML file, but I could not find a TOML reading library.
# JSON looks terrible and doesn't allow for commenting parts (examples) out.


# LED pins - differ bgetween displaypack2.0 and displaypack 2.8
# Comment out the one you're not using :
hardware = {
    # For Display Pack and Display Pack 2.0":
    # "LED_pins" : [ 6, 7, 8 ],
    # For Display Pack 2.8":
    "LED_pins" : [ 26, 27, 28 ],
}

# matching 1 wire sensor unique IDs to human sensible values
one_wire_sensor = {
    "thermometer" : {
            # "0123456789"  :  "Living Room",
            # "1234567890"  :  "Bed Room",
    }
}
