# access-control-rfid-nfc

> [!WARNING]  
> This project is being reworked, there are a lot of issues from the port to the new architecture  
> There are a lot of possible exploits, please be aware.

## How to run it

### Install packages

```bash
python3 -m venv venv
pip install -r requirements.txt
```

#### Migrations

```bash
FLASK_MIGRATE=1 flask db upgrade
```

If you want to edit the `models.py` file, you will need to create migrations and apply them by running:

```bash
FLASK_MIGRATE=1 flask db migrate && FLASK_MIGRATE=1 flask db upgrade
```

### Open the WebUI

Go to [http://localhost:5000](http://localhost:5000) and login with the user `admin:password`

## Run tests

In 2 different terminals

```
DATABASE_URI=sqlite:/// python3 app.py
```

```
pytest -vs
```