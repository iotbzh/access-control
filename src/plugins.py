import importlib
import glob
import os
import threading

class Plugins:

    plugins_folder = "plugins"

    @classmethod
    def init_all(cls, app):
        for module_folder in glob.glob(f"{cls.plugins_folder}/*"):
            if not os.path.isdir(module_folder):
                continue
            module_name = os.path.basename(module_folder)
            bp = importlib.import_module(f"{cls.plugins_folder}.{module_name}").bp
            app.register_blueprint(bp)
            print(f" * {module_name} plugin loaded !")