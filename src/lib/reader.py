from src.models import Reader

class BaseReader:
    reader: Reader
    
    def __init__(self, reader, **kwargs):
        self.reader = reader
        print(self.__annotations__)
        for config in self.__annotations__:
            print(config)
            setattr(self, config, kwargs.get(config))