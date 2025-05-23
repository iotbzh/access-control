import pytest

def test_create_role(admin_client):
    admin_client.post("/roles/add", data={
        "name": "users",
        "access_start": "08:00",
        "access_end": "18:00",
        "access_days": [
            "0", "1", "2", "3", "4", "5"
        ]
    })

    rv = admin_client.get("/roles")
    assert "users" in rv.text

@pytest.mark.order(after="test_create_role")
def test_config_readers(admin_client):
    admin_client.post("/roles/readers/1", data={
        "readers": "1"
    })

    rv = admin_client.get("/roles/readers/1")
    assert "checked" in rv.text

@pytest.mark.order(after="test_users.py::test_user_edit")
def test_role_edit(admin_client):
    admin_client.post("/roles/edit/1", data={
        "name": "users",
        "access_start": "07:00:00",
        "access_end": "19:00:00",
        "access_days": [
            "0","1","2","3","4","5","6"
        ]
    })

    rv = admin_client.get("/roles")
    assert "19:00:00" in rv.text and "07:00:00" in rv.text