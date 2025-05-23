from src.lib.gateway import BaseGateway
from src.lib.reader import BaseReader

class Gateway(BaseGateway):
    uid = "example-gateway"
    name = "Example Gateway"
    reader_class = BaseReader
    
    class Config:
        connect_message: str = "Connecting to"
    
    @staticmethod
    def connect(reader):
        print(Gateway.get_var("connect_message"), reader.__class__)

    @staticmethod
    def disconnect(reader):
        print("Bye", reader.__class__)