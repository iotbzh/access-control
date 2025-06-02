import pytest
from datetime import datetime, timedelta

@pytest.mark.order(after="test_readers.py::test_reader_delete")
def test_access_authorized(admin_client):
    admin_client.post("/readers/add", data={
        "name": "desk",
        "description": "This reader is literaly in front of me",
        "is_active": "on",
        "gateway": "example-gateway"
    })

    admin_client.post("/roles/readers/1", data={
        "readers": "1"
    })

    rv = admin_client.get("/tests/access/example-gateway/1/cc39a284bed549c5cdc3a61ed9e63c7a")

    assert rv.text == "True"

@pytest.mark.order(after="test_access_authorized")
def test_access_access_start_unauthorized(admin_client):

    now = datetime.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    access_start = current_hour + timedelta(hours=1)
    access_end = current_hour + timedelta(hours=2)
    access_start_str = access_start.strftime("%H:%M:%S")
    access_end_str = access_end.strftime("%H:%M:%S")

    admin_client.post("/roles/edit/1", data={
        "name": "users",
        "access_start": access_start_str,
        "access_end": access_end_str,
        "access_days": [
            "0","1","2","3","4","5","6"
        ]
    })

    rv = admin_client.get("/tests/access/example-gateway/1/cc39a284bed549c5cdc3a61ed9e63c7a")

    assert rv.text == "False"

@pytest.mark.order(after="test_access_access_start_unauthorized")
def test_access_access_end_unauthorized(admin_client):

    now = datetime.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    access_start = current_hour - timedelta(hours=2)
    access_end = current_hour - timedelta(hours=1)
    access_start_str = access_start.strftime("%H:%M:%S")
    access_end_str = access_end.strftime("%H:%M:%S")

    admin_client.post("/roles/edit/1", data={
        "name": "users",
        "access_start": access_start_str,
        "access_end": access_end_str,
        "access_days": [
            "0","1","2","3","4","5","6"
        ]
    })

    rv = admin_client.get("/tests/access/example-gateway/1/cc39a284bed549c5cdc3a61ed9e63c7a")

    assert rv.text == "False"

@pytest.mark.order(after="test_access_access_end_unauthorized")
def test_access_reader_unauthorized(admin_client):

    now = datetime.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    access_start = current_hour - timedelta(hours=2)
    access_end = current_hour + timedelta(hours=2)
    access_start_str = access_start.strftime("%H:%M:%S")
    access_end_str = access_end.strftime("%H:%M:%S")

    admin_client.post("/roles/edit/1", data={
        "name": "users",
        "access_start": access_start_str,
        "access_end": access_end_str,
        "access_days": [
            "0","1","2","3","4","5","6"
        ]
    })

    admin_client.post("/roles/readers/1", data={
        "readers": ""
    })

    rv = admin_client.get("/tests/access/example-gateway/1/cc39a284bed549c5cdc3a61ed9e63c7a")

    assert rv.text == "False"

@pytest.mark.order(after="test_access_reader_unauthorized")
def test_access_deactivation_date_unauthorized(admin_client):

    admin_client.post("/roles/readers/1", data={
        "readers": "1"
    })

    admin_client.post("/badges/edit/1", data={
        "uid": "cc39a284bed549c5cdc3a61ed9e63c7a",
        "user_id": "1",
        "role": "1",
        "deactivation_date": "1992-10-03",
        "guest_name": "Guest Name",
        "company_name": "Campany Name"
    })

    rv = admin_client.get("/tests/access/example-gateway/1/cc39a284bed549c5cdc3a61ed9e63c7a")

    assert rv.text == "False"