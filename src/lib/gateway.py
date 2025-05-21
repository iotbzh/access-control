class BaseGateway:
    uid = "unknown"
    name = "Unknown"
    reader_class = None

    configs = []

    @staticmethod
    def connect(reader):
        pass

    @staticmethod
    def job(reader, on_badge):
        pass

    @staticmethod
    def action(reader, authorized, badge_uid): # TODO: Rename this method...
        pass