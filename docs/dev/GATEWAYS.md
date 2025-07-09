# Developper Documentation - Gateways

This documention use a fake reader API, everything imported from `reader_api` is only for example purpose

## Basic Usage

This code will create a basic Gateway with no fonctionnality.

`gateways/example/__init__.py`
```py
from src.lib.gateway import BaseGateway
from src.lib.reader import BaseReader

class Gateway(BaseGateway):
    uid = "example-gateway"
    name = "Example Gateway"
    reader_class = BaseReader
```

## Connecting to reader

When a reader is added to the Gateway it triggers the `connect` method with an instance of the `reader_class`

`gateways/example/__init__.py`
```py
class Gateway(BaseGateway):
    ...

    @staticmethod
    def connect(reader):
        print("Connecting to", reader.__class__)
        return True # Return True if reader connected
```

## Disconnecting the reader

Sometimes the Gateway is reloaded, like when configuration is changed, in this case, every reader are disconnected then reconnected, if you're using communication methods like socket, you will need to close them in the `disconnect` method.

`gateways/example/__init__.py`
```py
class Gateway(BaseGateway):
    ...

    @staticmethod
    def disconnect(reader):
        print("Bye", reader.__class__)
```

## Job

The Gateway job is a thread that call a function when he receive a badge, there is one job per readers, and when you find a badge you need to call the callback set in params.

`gateways/example/__init__.py`
```py
from reader_api import wait_for_badge

class Gateway(BaseGateway):
    ...

    @staticmethod
    def job(reader, on_badge):
        while reader.running:
            badge_uid = wait_for_badge()
            on_badge(badge_uid)
```

## Event

The `event` method is executed when a reader needs to open the door after executing `on_badge`

`gateways/example/__init__.py`
```py
from reader_api import open_door, refuse_access

class Gateway(BaseGateway):
    ...

    @staticmethod
    def event(reader, authorized, badge_uid):
        if authorized:
            open_door()
        else:
            refuse_access()
```

## Gateway Configuration

This will create a string variable that can be configured on the webui at `/gateways/example-gateway`

`gateways/example/__init__.py`
```py
class Gateway(BaseGateway):
    ...

    class Config:
        connect_message: str = "Connecting to"
    
    @staticmethod
    def connect(reader):
        print(Gateway.get_var("connect_message"), reader.__class__)
```

## Reader class

To store data or add functionnalities to your reader you can create a custom Reader class, you can add reader configuration directly as an attribute, don't forget to type it, it use `__annotations__` to find the variables, so if you want a variable to not show in the reader configuration you just have to remove the type, or init it in a `__init__` method.

`gateways/example/__init__.py`
```py
class Reader(BaseReader):
    ip: str = "127.0.0.1"

class Gateway(BaseGateway):
    ...
    reader_class = Reader
```

## Reader class init

`gateways/example/__init__.py`
```py
class Reader(BaseReader):
    ip: str = "127.0.0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "ExampleReader"

class Gateway(BaseGateway):
    ...
    reader_class = Reader

    @staticmethod
    def connect(reader: Reader):
        print(f"Hello {reader.name} ({reader.ip})")
```

## Actions

It allows you to connect the web interface with the Gateway, there are ActionButton and Action. ActionButtons can be found in the map, they are direct connection from ui to gateway, Actions can be accessed using an API call, this is when you want to interract with your gateway through a plugin. For `Action` only `gateway` is required, you can add as many attributes after

`gateways/example/__init__.py`
```py
class Gateway(BaseGateway):
    ...
    
    class Actions:
        @ActionButton("Say Hello")
        def say_hello(gateway, reader):
            print(f"Hello {reader.name}")

        @Action()
        def say_custom_hello(gateway, reader_name, message): 
            print(f"{message} {reader_name}")
```