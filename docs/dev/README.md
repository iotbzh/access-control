# Developper Documentation

## Project architecture

As a developper most of your work will be done inside the `gateways/` and `plugins/`, but if you need to go deeper inside the app you still see the code inside `src/`

### `src/`

This is where most of the code is, the goal is to have a modular system with Gateways and Plugins

#### `src/controllers/`

This is where controllers are stored, controllers manage data, actions, and templating. They should be imported in the `app.py` like that:

```py
from src.controllers.users import bp as users_controller

app.register_blueprint(users_controller)
```

#### `src/lib/`

This is where classes and definitions for Gateways and Plugin are

### `templates/`

This folder contains all templated HTML, each controller have a folder.

### `static/`

Contains static files like CSS or Images for the client side

### `gateways/`

This folder contains all Gateways, each gateway have a folder like `test-gateway/` and a `__init__.py` which is the entry point.

### `plugins/`

This folder is very similar to Gateways

## Concepts

### Controller

It's like a manager for an object, for example the User controller have the code for the listing rendering, for editing and creation, everything which involve User should be in it, unless it involve an other object, in this case you can choose where to put it.

### Model

A model is a table in the database, by importing the class you can use the ORM to execute commands for the table like `select` or `update`

### Addons

A git repository that contain multiple Gateways or Plugins or both, they can be imported and updated 

### Gateways

To connect a reader to the server you need to use or create a Gateway. A Gateway consist of multiple required or optional parts, the Gateway class, the Reader class, the Gateway Config and Gateway Actions.

### Plugins

Thanks to plugins you can create web interfaces for custom and possibly non-related actions or informations, you can use them to have access to your coffee machine water for example.