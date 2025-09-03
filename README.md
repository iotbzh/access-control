# Access Control

A universal badge access control server, designed to work with any reader and any badge.
Thanks to powerful gateways and a flexible plugin system, you can integrate your own readers into the server, use community-made addons, or develop your own.

> This server is field-tested and already used in companies.

### Features:

- [x] Full control stack (Users, badges, roles, readers)
- [x] Complete access configuration (Hours, days, doors, deactivation times)
- [x] Interactive map
- [x] LDAP user synchronization and admin permission checks
- [x] OpenID login support
- [x] SMTP integration
- [x] Non-admin user interface
- [x] Customization via addons

## How to run it

### Install packages

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### Init database

The 1st time, you need to run migrations, knowing that the first migration include tables creation.

```bash
flask db upgrade
```

### Run the app

No need to use an other WSGI for production, it already uses `gevent`.
You will need to create a `.env`, you can use the `.env.example` as example.

```
python3 app.py
```

### Open the WebUI

Go to [http://localhost:5000](http://localhost:5000) and login with the user `admin:password` (You can modify the `.env` to change the admin password)

## Run tests

In 2 different terminals

```
DATABASE_URI=sqlite:/// python3 app.py
```

```
pytest -vs
```


## Development

### Migrations

If you want to edit the `models.py` file, you will need to create migrations

```bash
FLASK_MIGRATE=1 flask db migrate
```
