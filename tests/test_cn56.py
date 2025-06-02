import pytest
import time

@pytest.mark.order(after="test_readers.py::test_empty_reader_list")
def test_create_cn56_reader(admin_client):
    admin_client.post("/readers/add", data={
        "name": "desk",
        "description": "This reader is literaly in front of me",
        "is_active": "on",
        "gateway": "cn56-gateway"
    })

    rv = admin_client.get("/readers")
    assert """This reader is literaly in front of me""" in rv.text

@pytest.mark.order(after="test_create_cn56_reader")
def test_config_cn56_reader(admin_client):
    admin_client.post("/readers/edit/1", data={
        "name": "desk",
        "description": "This reader is literaly in front of me",
        "is_active": "on",
        "gateway": "cn56-gateway",
        "gateway-device_address": "0",
        "gateway-ip": "172.25.50.40",
        "gateway-can_write": "on"
    })

    rv = admin_client.get("/readers")
    assert "Online" in rv.text

@pytest.mark.order(after="test_config_cn56_reader")
def test_map_action(admin_client):
    rv = admin_client.post("/actions/map/cn56-gateway/hello_world/1")
    assert "<!DOCTYPE html>" in rv.text

@pytest.mark.order(after=["test_map_action", "test_badges.py::test_create_badge"])
def test_valid_reader_scan(admin_client):
    for i in range(10):
        rv = admin_client.get("/logs")
        if "cc39a284bed549c5cdc3a61ed9e63c7a" in rv.text and "authorized" in rv.text:
            return
        time.sleep(1)
    assert "cc39a284bed549c5cdc3a61ed9e63c7a" in rv.text and "authorized" in rv.text

# Removed for tests
# @pytest.mark.order(after="test_valid_reader_scan")
# def test_invalid_reader_scan(admin_client):
#     for i in range(10):
#         rv = admin_client.get("/logs")
#         if "c0ffee00000000000000000000000000" in rv.text and "denied" in rv.text:
#             return
#         time.sleep(1)
#     assert "c0ffee00000000000000000000000000" in rv.text and "denied" in rv.text

def test_config_gateway_key(admin_client):
    admin_client.post("/gateways/cn56-gateway", data={
        "key": "44000000000000000000000000000033",
        "ip": "172.25.50.124"
    })

    rv = admin_client.get("/gateways/cn56-gateway")
    assert "44000000000000000000000000000033" in rv.text