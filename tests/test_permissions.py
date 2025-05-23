import pytest
# from app import app

@pytest.fixture
def checked_routes():
    return []

def check_login_redirect(client, checked_routes, url):
    """Check if ther user is redirected to /login?next=* when going to a login required page"""
    checked_routes.append(url)
    rv = client.get(url)
    assert rv.url.endswith(f"/login?next={url}") 

def test_home(client, checked_routes):
    check_login_redirect(client, checked_routes, "/")

# def test_all_checked(checked_routes):
#     output = []
#     for rule in app.url_map.iter_rules():
#         url = str(rule)
#         print(url)
#         assert url in checked_routes