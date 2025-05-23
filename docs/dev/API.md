# Developper Documentation - API

There are a lot of APIs that can be used in Gateways/Plugins, this page will show most of them

## Auth

```py
from src.auth import *
```

### `@login_required`

This decorator allows you to make a route or a function only accessible to logged users, when not logged the user will be redirected to the login page

```py
@app.route('/')
@login_required
def index():
    return "Hello World!"
```

### `@admin_required`

This the same as `@login_required` but for admins

```py
@app.route('/')
@admin_required
def index():
    return "Hello World!"
```

### `current_user(): dict`

Returns `session.get("user")`, with `flask.session`

```py
@app.route('/')
@login_required
def index():
    user = current_user()
    return f"Hello, {user.username}"
```

### `is_admin(user: dict): bool`

`user`: User data stored in the flask session

```py
@app.route('/')
@login_required
def index():
    if is_admin(current_user()):
        return "You're admin"
    return "You're not admin"
```

## Configs

## Models

Uses `flask_sqlalchemy`

```py
from src.models import *
```

## Database & Database session

Those objects are named `db` and `dbs`

## Schedules

```py
from src.schedules import *
```

### `@app_schedule`

When you need to use the app context inside a schedule you can use this decorator

```py
import schedule

@app_schedule
def my_schedule():
    readers = dbs.execute(db.select(Reader)).scalars().all()
    print(len(readers))

schedule.every(1).minutes.do(my_schedule)
```

## SMTP

```py
from src.smtp import SMTP
```

### `SMTP.send_to(to: list[str], subject: str, content: str)`

```py
SMTP.send_to(
    ["user1@iot.bzh", "user2@iot.bzh"], 
    "This is the subject", 
    "This is the content\n\nSent by the access control server"
)
```

## Socketio

```py
from src.socketio import sock
```

## `@sock.on(event: str)`

```py
@sock.on("update")
@login_required
def on_update():
    sock.emit("data", get_updated_data())
```