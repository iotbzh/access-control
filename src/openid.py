from src.settings import Settings
from authlib.integrations.flask_client import OAuth

app = None # Should be the in the app.py
oauth = None

def get_oauth():
    global oauth 

    if not Settings.get("openid_enabled"):
        return None

    if oauth:
        return oauth

    oauth = OAuth(app)

    oauth.register(
        name='openid_app',
        client_id=Settings.get("openid_client_id"),
        client_secret=Settings.get("openid_client_secret"),
        server_metadata_url=Settings.get("openid_metadata_url"),
        client_kwargs={'scope': 'openid profile roles email'},
    )
    return oauth