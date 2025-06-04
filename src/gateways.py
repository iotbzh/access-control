import importlib
import glob
import os
import threading
import time
from flask import current_app, Flask

from src.models import db, dbs, Gateway, Reader
from src.access import access_control
from src.configs import Configs

class Gateways:

    gateways_folder = "gateways"
    gateways = {}
    app: Flask = None # A global reference to the flask app

    @classmethod
    def init_all(cls):
        for module_folder in glob.glob(f"{cls.gateways_folder}/*"):
            # If not directory or have "__" in the name like __pycache__
            if not os.path.isdir(module_folder) or "__" in module_folder:
                continue
            # Get the module_name from the filename
            module_name = os.path.basename(module_folder)
            cls.import_gateway(module_name)
    
    @classmethod
    def import_gateway(cls, module_name):
        gateway = importlib.import_module(f"{cls.gateways_folder}.{module_name}").Gateway

        # If not stored, store the gateway class
        if gateway.uid not in cls.gateways:
            cls.gateways[gateway.uid] = gateway
        
        # Add default config and add it to the DB
        if not dbs.execute(db.select(Gateway).where(Gateway.uid == gateway.uid)).scalar_one_or_none():
            default_config = Configs.get_default_config(gateway.Config)
            dbs.add(Gateway(uid=gateway.uid, name=gateway.name, configs=default_config))
            dbs.commit()
    
        cls.init_gateway(gateway.uid)

    @classmethod
    def init_gateway(cls, gateway_uid):
        readers = dbs.execute(db.select(Reader).where(Reader.gateway == gateway_uid)).scalars().all()
        gateway = cls.gateways.get(gateway_uid)

        # For each readers, extract reader from context and initialize it
        for reader in readers:
            dbs.expunge(reader)
            try:
                cls.init_reader(gateway, reader)
            except Exception as e:
                print(f"Could not initialize reader: {e}")
        
        print(f" + {gateway_uid} gateway loaded !")

    @classmethod
    def init_reader(cls, gateway, reader):
        with cls.app.app_context():
            # If readers was already initied, disconnect and clear
            if gateway.readers.get(reader.id):
                gateway.disconnect(gateway.readers.get(reader.id))
                del gateway.readers[reader.id]
            
            if not reader.is_active:
                return
            
            # Create reader instance and try to connect 
            reader_instance = gateway.reader_class(reader, **reader.gateway_configs)
            gateway.readers[reader.id] = reader_instance
            success = gateway.connect(reader_instance)

            if not success:
                return

            # Decorator to keep gateway and reader_instance values
            def reader_context(gateway, reader_instance):
                def decorator(func):
                    def wrapper(*args, **kwargs):
                        return func(gateway, reader_instance, *args, **kwargs)
                    return wrapper
                return decorator
            
            # Callback executed by gateway when getting badge uid
            @reader_context(gateway, reader_instance)
            def on_badge(gateway, reader_instance, badge_uid):
                with cls.app.app_context():
                    access_control(gateway, reader_instance, badge_uid)

            threading.Thread(target=gateway.job, args=(reader_instance, on_badge), daemon=True).start()

    @classmethod
    def get(cls, gateway_uid):
        return cls.gateways.get(gateway_uid)