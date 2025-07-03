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
