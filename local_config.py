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
     "air" : "28e81dfb050000d6",
     "cup" : "28828beb050000c9",
     "back yard" : "28c12cfb050000bf",
     "Alien Moon" : "287a10ea05000052",
     "Bikers Mitt" : "28d9aa2c06000071",
     "Cauldron" : "2865b3e9050000d8",
     "default" : "28e81dfb050000d6",
}

# Logs to create :
log_files = {
    "24 hours bme" : {"log interval" : 720,
                      "keys" : ["bme temperature", "pressure", "humidity"],
                      "max records" : 135, # Number of records to hold in memory (plus buffer size)
                      "buffer size" : 1, # Number of records to add between writes and truncating to max records
                      },
    "24 hours ds18b20" : {"log interval" : 720,
                      "keys" : ["Alien Moon", "Bikers Mitt", "Cauldron",],
                      "max records" : 135, # Number of records to hold in memory (plus buffer size)
                      "buffer size" : 5, # Number of records to add between writes and truncating to max records
                      },
    "12 hours bme" : {"log interval" : 360,
                      "keys" : ["bme temperature", "pressure", "humidity"],
                      "max records" : 135, # Number of records to hold in memory (plus buffer size)
                      "buffer size" : 3, # Number of records to add between writes and truncating to max records
                      },
    "12 hours ds18b20" : {"log interval" : 360,
                          "keys" : ["Alien Moon", "Bikers Mitt", "Cauldron",],
                          "max records" : 135, # Number of records to hold in memory (plus buffer size)
                          "buffer size" : 3, # Number of records to add between writes and truncating to max records
                          },
    "Last hour bme" : {"log interval" : 30,
                       "keys" : ["bme temperature", "humidity"],
                       "max records" : 135, # Number of records to hold in memory (plus buffer size)
                       "buffer size" : 10, # Number of records to add between writes and truncating to max records
                       },
    "Last hour ds18b20" : {"log interval" : 30,
                           "keys" : ["Alien Moon", "Bikers Mitt", "Cauldron",],
                           "max records" : 135, # Number of records to hold in memory (plus buffer size)
                           "buffer size" : 20, # Number of records to add between writes and truncating to max records
                           },
    "Ram Usage" : {"log interval" : 120,
                   "keys" : ["PreCollect", "PostCollect"],
                   "max records" : 135, # Number of records to hold in memory (plus buffer size)
                   "buffer size" : 10, # Number of records to add between writes and truncating to max records
                   },
    }

# Graphs to plot :
graph_ranges = {
    # "Big Dave" : {"marker scale" : "hours",
    #               "units" : "mb",
    #               "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
    #               "keys" : ["pressure"],
    #               "logs" : ["24 hours bme"],
    #               },
    "12H Pressure" : {"marker scale" : "hours",
                      "units" : "hPa",
                      "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
                      "keys" : ["pressure"],
                      "logs" : ["12 hours bme"],
                      },
    "12H Temp" : {"marker scale" : "hours",
                      "units" : "c",
                      "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
                      "keys" : ["bme temperature"],
                      "logs" : ["12 hours bme"],
                      },
    "12H Humidity" : {"marker scale" : "hours",
                      "units" : "%",
                      "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
                      "keys" : ["humidity"],
                      "logs" : ["12 hours bme"],
                      },
                       
    "12 hrs ds18b20" : {"marker scale" : "hours",
                  "units" : "C",
                  "markers" : [0, 3, 6, 9, 12, 15, 18, 21],
                  "keys" : ["Alien Moon", "Bikers Mitt", "Cauldron", "bme temperature",],
                  "logs" : ["12 hours ds18b20", "12 hours ds18b20"],
                  },
    "Last hour" : {"marker scale" : "mins",
                   "units" : "C",
                   "markers" : [0, 15, 30, 45],
                   "keys" : ["Alien Moon", "Bikers Mitt", "Cauldron", "bme temperature",],
                   "logs" : ["Last hour ds18b20", "Last hour bme"],
                  },
    "24 hours" : {"marker scale" : "hours",
                  "units" : "c",
                  "markers" : [0, 6, 12, 18],
                  "keys" : ["Alien Moon", "Bikers Mitt", "Cauldron", "bme temperature",],
                  "logs" : ["24 hours ds18b20", "24 hours bme"],
                  },
    "Ram Usage" : {"marker scale" : "mins",
                   "units" : "%",
                   "markers" : [0, 15, 30, 45],
                   "keys" : ["PreCollect", "PostCollect"],
                   "logs" : ["Ram Usage"],
                   },
    }