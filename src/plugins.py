import importlib
import glob
import os
import threading

from src.models import db, dbs, Plugin
from src.configs import Configs

class Plugins:

    plugins_folder = "plugins"
    plugins = {}

    @classmethod
    def init_all(cls, app):
        for plugin_uid in cls.get_all_plugins():
            plugin = cls.plugins[plugin_uid]
            app.register_blueprint(plugin.bp)
            print(f" + {plugin.uid} plugin loaded !")
    
    @classmethod
    def get_all_plugins(cls):
        for module_folder in glob.glob(f"{cls.plugins_folder}/*"):
            if not os.path.isdir(module_folder) or "__" in module_folder:
                continue
            module_name = os.path.basename(module_folder)
            plugin = importlib.import_module(f"{cls.plugins_folder}.{module_name}").Plugin
            bp = plugin.bp
            configs = plugin.Config

            if plugin.uid not in cls.plugins:
                cls.plugins[plugin.uid] = plugin
            
            if not dbs.execute(db.select(Plugin).where(Plugin.uid == plugin.uid)).scalar_one_or_none():
                default_config = Configs.get_default_config(configs)
                dbs.add(Plugin(uid=plugin.uid, configs=default_config))
        
        dbs.commit()
        return cls.plugins
    
    @classmethod
    def get(cls, plugin_uid):
        return cls.plugins.get(plugin_uid)