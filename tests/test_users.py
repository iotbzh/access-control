def test_create_user(admin_client):
    admin_client.post("/users/add", data={
        "uid": "alex",
        "name": "Alex",
        "email": "alex.zalo+pytest@iot.bzh",
        "is_active": "on"
    })

    rv = admin_client.get("/users")
    assert "alex.zalo+pytest@iot.bzh" in rv.text

def test_user_badges(admin_client):
    rv = admin_client.get("/users/badges/1")
    assert "cc39a284bed549c5cdc3a61ed9e63c7a" in rv.text

def test_user_edit(admin_client):
    rv = admin_client.post("/users/edit/1", data={
        "uid": "azalo",
        "name": "Alex",
        "email": "alex.zalo+pytest@iot.bzh"
    })
    assert "<td>azalo</td>" in rv.text and '<span class="badge bg-danger">' in rv.text

def test_create_and_delete_user(admin_client):
    admin_client.post("/users/add", data={
        "uid": "test123",
        "name": "Test",
        "email": "alex.zalo+pytest@iot.bzh",
        "is_active": "on"
    })

    rv = admin_client.get("/users")
    assert "<td>test123</td>" in rv.text

    rv = admin_client.post("/users/delete/2")
    assert "<td>test123</td>" not in rv.text