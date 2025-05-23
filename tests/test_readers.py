import pytest

def test_empty_reader_list(admin_client):
    rv = admin_client.get("/readers")
    assert """<tbody>
        
    </tbody>""" in rv.text

@pytest.mark.order(after="test_cn56.py::test_valid_reader_scan")
def test_reader_edit(admin_client):
    admin_client.post("/readers/edit/1", data={
        "name": "desk",
        "description": "Description test",
        "gateway": "cn56-gateway",
        "gateway-device_address": "0",
        "gateway-ip": "172.25.50.40",
        "gateway-can_write": "on"
    })

    rv = admin_client.get("/readers")
    assert "Description test" in rv.text and '<span class="badge bg-danger">' in rv.text

@pytest.mark.order(after="test_reader_edit")
def test_reader_delete(admin_client):
    admin_client.post("/readers/delete/1")
    rv = admin_client.get("/readers")
    assert """<tbody>
        
    </tbody>""" in rv.text