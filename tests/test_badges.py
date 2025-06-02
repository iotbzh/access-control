import pytest

@pytest.mark.order(after=[
    "test_users.py::test_create_user", 
    "test_roles.py::test_create_role"
])
def test_create_badge(admin_client):
    admin_client.post("/badges/add", data={
        "uid": "cc39a284bed549c5cdc3a61ed9e63c7a",
        "user_id": "1",
        "role": "1",
        "is_active": "on",
        "deactivation_date": "",
        "guest_name": "",
        "company_name": ""
    })

    rv = admin_client.get("/badges")
    assert "cc39a284bed549c5cdc3a61ed9e63c7a" in rv.text

@pytest.mark.order(after="test_cn56.py::test_valid_reader_scan")
def test_badge_edit(admin_client):
    admin_client.post("/badges/edit/1", data={
        "uid": "cc39a284bed549c5cdc3a61ed9e63c7a",
        "user_id": "1",
        "role": "1",
        "deactivation_date": "1992-10-03",
        "guest_name": "Guest Name",
        "company_name": "Campany Name"
    })

    rv = admin_client.get("/badges")
    assert "<td>Guest Name</td>" in rv.text and "<td>Campany Name</td>" in rv.text and '<span class="badge bg-danger">' in rv.text