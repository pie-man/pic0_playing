""" Class to handle log files stored to disc.

Each instance has a max no of records, and a filename.
Methods to open, append, clip and close files"""
import os

class Daniel(object):

    def __init__(self, filename: str, max_len: int, buffer_len: int, keys: list[str]):
        self.name = filename
        self.max_len = max_len
        self.buffer_len = buffer_len
        self.keys = keys
        self.record_len = len(keys)
        self.data = []
        try:
            print("Starter for 10")
            fh = open(filename, "r")
            print("open")
            fh.close()
            print("close")
            self.read_data()
            print("read")
            # self.current_len = len(self.data)
            print(f"Opened file {filename} and  read {len(self.data)} records")
        except:
            self.current_len = 0
            print(f"something failed trying to open file {filename}")
        print("The dust is settling")
        self.current_len = len(self.data)

    def add_record(self, data_dict, len_check=True):
        """Passed a dictionary of name:value data pairs, stores those where 'name' exists
        in the predefined self.keys list, and stores a None for items in self.keys not matched
        by a name in the data dict. Things named in the data dict, but not included in self.keys
        are ultimately discarded in this operation.
        Creating a single list containing just values and Nones, in the order described by self.keys,
        which forms a 'record', this is then appended to self.data"""
        data_record = []
        for thing in self.keys:
            if thing in data_dict:
                data_record.append(data_dict[thing])
            else:
                data_record.append(None)
        self.data.append(data_record)
        if len_check and len(self.data) > self.max_len + self.buffer_len:
            self.data = self.data[0-self.max_len:]
            self.write_data()

    def read_data(self):
        """Opens the file refferred to by self.name and reads it in.
        The assumption is that the first line describes what the entities in the file are, then each subsequent line
        is a single record for all those entities.
        These are assembled into a dictionary or named values and then passed to the add_record routine where those values
        selected in self.keys will become part of a record, and those not given in self.keys will be discarded
        Ultimately this allows for changes in mind of the contents of data logs with the potential to discard data types
        no longer used, and populate historic records with None entries when new data types are added."""
        print("reading...")
        with open(self.name, "r") as fh:
            print("open..")
            keys_as_text = fh.readline().strip()
            print(f"read keys as : {keys_as_text}")
            file_keys = keys_as_text.split(",")
            data_read = 0
            for line in fh:
                print(f"reading a line: {line}")
                data_dict = {}
                data_vals = line.rstrip().split(",")
                print(f"Data vals point 1 = {data_vals}")
                data_vals = [x if x !="no value" else None for x in data_vals]
                print(f"Data vals point 2 = {data_vals}")
                for count, thing in enumerate(file_keys):
                    print(f"Belt n braces, count is {count}")
                    print(f"Setting {thing} to {data_vals[count]}")
                    data_dict[thing] = data_vals[count]
                self.add_record(data_dict, len_check=False)
                data_read += 1
                print(f"read {data_read} bits of data")

    def write_data(self):
        """Opens an empty file (potentially overwriting), and dumps the latest self.max_len records
        of data curently held in self.data to it, effectively 'trimming' the file length if/when it exceeds
        self.max_len.
        The first line of the file will be the names of the data types defined by self.keys"""
        description_text = ",".join(self.keys) + "\n"
        with open(self.name, "w") as fh:
            fh.write(description_text)
            for record in self.data[0-self.max_len:]:
                record_as_text = [f"{x}" if x else "no record" for x in record]
                fh.write(f"{",".join(record_as_text)}\n")

    