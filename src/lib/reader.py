from src.models import Reader

class BaseReader:
    reader = None
    running = False
    
    def __init__(self, reader, **kwargs):
        self.reader = reader
        self.is_online = False
        for config in self.__class__.__annotations__:
            setattr(self, config, kwargs.get(config))