import subprocess
import time
import pytest
import os
import signal
import threading
import requests

class Client(requests.Session):
    def request(self, *args, **kwargs):
        if len(args) > 1:
            largs = list(args)
            largs[1] = "http://localhost:5000" + args[1]
            args = tuple(largs)
        else:
            kwargs["url"] = "http://localhost:5000" + kwargs["url"]
        # print(args, kwargs)
        return super().request(*args, **kwargs)

@pytest.fixture(scope="session")
def client():
    return Client()

@pytest.fixture(scope="session")
def admin_client():
    client = Client()
    client.post("/login", {
        "username": "admin",
        "password": "password"
    })
    return client