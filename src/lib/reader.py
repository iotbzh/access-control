from src.models import Reader

class BaseReader:
    reader = None
    running = False
    
    def __init__(self, reader, **kwargs):
        self.reader = reader
        self.is_online = False
        print(self.__class__.__annotations__)
        for config in self.__class__.__annotations__:
            print(config)
            setattr(self, config, kwargs.get(config))