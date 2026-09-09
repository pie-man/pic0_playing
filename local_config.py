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
    "WiFi" : True
}

# matching 1 wire sensor unique IDs to human sensible values
one_wire_sensor = {
     "mug" : "28b9fefa050000d4",
     "cup" : "28e81dfb050000d6",
     "air" : "28828beb050000c9",
     "back yard" : "28c12cfb050000bf",
     "default" : "28e81dfb050000d6",
}

# Logs to create :
log_files = {
    "24 hours bme" : {"log interval" : 720,
                      "keys" : ["bme temperature", "pressure", "rel_humidity"],
                      },
    "Last hour bme" : {"log interval" : 30,
                       "keys" : ["bme temperature", "pressure", "rel_humidity"]
                       },
    "Last hour ds18b20" : {"log interval" : 30,
                           "keys" : ["mug", "back yard"]
                           },
    "12 hours" : {"log interval" : 360,
                  "keys" : ["bme temperature", "mug", "cup", "air"],
                  },
    "Ram Usage" : {"log interval" : 120,
                   "keys" : ["PreCollect", "PostCollect"],
                   },
    }

# Graphs to plot :
graph_ranges = {
    "24 hours" : {"marker scale" : "hours",
                  "markers" : [0, 6, 12, 18],
                  "keys" : ["cpu temperature", "bme temperature"],
                  "logs" : ["24 hours bme"],
                  },
    "Last hour" : {"marker scale" : "mins",
                   "markers" : [0, 15, 30, 45],
                   "keys" : ["mug", "back yard"],
                   "logs" : ["Last hour ds18b20"],
                  },
    "12 hours" : {"marker scale" : "hours",
                  "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
                  "keys" : ["bme temperature", "mug", "cup", "air"],
                  "logs" : ["12 hours"],
                  },
    "Ram Usage" : {"marker scale" : "mins",
                   "markers" : [0, 15, 30, 45],
                   "keys" : ["PreCollect", "PostCollect"],
                   "logs" : ["Ram Usage"],
                   },
    }