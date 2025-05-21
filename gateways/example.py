from src.lib.gateway import BaseGateway
from src.lib.config import Config
from src.lib.reader import BaseReader

import os

class Reader(BaseReader):
    name: str

class Gateway(BaseGateway):
    enabled = True # Set it to false to hide the gateway
    # TODO: Add the feature...
    name = "Example Gateway"
    uid = "example-gateway"
    reader_class = Reader

    # Change this to a class and get variables from .__annotations__
    configs = [
        Config("Test String", str, "This is a test"),
        Config("Test Int", int, 2),
        Config("Test Boolean", bool, True)
    ]

    @staticmethod
    def connect(reader: Reader):
        open(f"{reader.name}.connect.txt", "w").write("Connect")
    
    @staticmethod
    def job(reader: Reader, on_badge):
        while True:
            if os.path.exists(f"{reader.name}.badge.txt"):
                badge_uid = open(f"{reader.name}.badge.txt", "r").read()
                os.remove(f"{reader.name}.badge.txt")
                on_badge(badge_uid)