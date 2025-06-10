import logging
from flask import Flask
import importlib
import glob
import os
import threading

from src.models import db, dbs, Plugin
from src.configs import Configs
from src.logger import Logger

class Plugins:

    plugins_folder = "plugins"
    plugins = {}
    app: Flask = None # A global reference to the flask app

    @classmethod
    def init_all(cls):
        for module_folder in glob.glob(f"{cls.plugins_folder}/*"):
            # If not directory or have "__" in the name like __pycache__
            if not os.path.isdir(module_folder) or "__" in module_folder:
                continue
                
            # Get the module_name from the filename
            module_name = os.path.basename(module_folder)
            cls.import_plugin(module_name)

    @classmethod
    def import_plugin(cls, module_name):
        plugin = importlib.import_module(f"{cls.plugins_folder}.{module_name}").Plugin

        # If not stored, store the plugin class
        if plugin.uid not in cls.plugins:
            cls.plugins[plugin.uid] = plugin
        
        # Add default config and add it to the DB
        if not dbs.execute(db.select(Plugin).where(Plugin.uid == plugin.uid)).scalar_one_or_none():
            default_config = Configs.get_default_config(plugin.Config)
            dbs.add(Plugin(uid=plugin.uid, configs=default_config))
            dbs.commit()
        
        Logger.init_plugin(plugin.uid)
        
        cls.init_plugin(plugin.uid)

    @classmethod
    def init_plugin(cls, plugin_uid):
        plugin = cls.plugins[plugin_uid]
        try:
            Plugins.app.register_blueprint(plugin.bp)
            logging.info(f" + {plugin.uid} plugin loaded !")
        except:
            logging.warning(f" - Cannot load plugin {plugin.uid}, please restart the server")
    
    @classmethod
    def get(cls, plugin_uid):
        return cls.plugins.get(plugin_uid)