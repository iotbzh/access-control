class BaseGateway:
    uid = "unknown"
    name = "Unknown"
    reader_class = None

    configs = []

    @staticmethod
    def connect(reader):
        pass

    @staticmethod
    def job(reader, on_card):
        pass