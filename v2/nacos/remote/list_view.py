class ListView:
    def __init__(self, data, count):
        self.data = data
        self.count = count

    def get_data(self):
        return self.data

    def get_count(self):
        return self.count

    def __str__(self):
        return "ListView{data=" + self.data + ", count=" + self.count + "}"
