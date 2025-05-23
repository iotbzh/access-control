import pytest

@pytest.mark.order(after="test_cn56.py::test_create_cn56_reader")
def test_map_update(admin_client):
    rv = admin_client.post("/map/update", json=[
        {
            "id": "1",
            "x": 500,
            "y": 500
        }
    ])
    assert rv.text == "{}\n"