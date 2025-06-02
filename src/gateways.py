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
    app: Flask = None

    @classmethod
    def get_all_gateways(cls):
        for module_folder in glob.glob(f"{cls.gateways_folder}/*"):
            if not os.path.isdir(module_folder) or "__" in module_folder:
                continue
            module_name = os.path.basename(module_folder)
            gateway = importlib.import_module(f"{cls.gateways_folder}.{module_name}").Gateway

            if gateway.uid not in cls.gateways:
                cls.gateways[gateway.uid] = gateway
            
            if not dbs.execute(db.select(Gateway).where(Gateway.uid == gateway.uid)).scalar_one_or_none():
                default_config = Configs.get_default_config(gateway.Config)
                dbs.add(Gateway(uid=gateway.uid, name=gateway.name, configs=default_config))
        
        dbs.commit()
        return cls.gateways
    
    @classmethod
    def init_all(cls, app):

        for gateway_uid in Gateways.get_all_gateways():
            readers = dbs.execute(db.select(Reader).where(Reader.gateway == gateway_uid)).scalars().all()
            gateway = cls.gateways.get(gateway_uid)

            for reader in readers:
                dbs.expunge(reader)
                cls.init_reader(app, gateway, reader)
            
            print(f" + {gateway_uid} gateway loaded !")

    @classmethod
    def init_reader(cls, app, gateway, reader):
        with app.app_context():
            if gateway.readers.get(reader.id):
                gateway.disconnect(gateway.readers.get(reader.id))
                del gateway.readers[reader.id]
            
            if not reader.is_active:
                return
            
            reader_instance = gateway.reader_class(reader, **reader.gateway_configs)
            gateway.readers[reader.id] = reader_instance
            success = gateway.connect(reader_instance)

            if not success:
                return

            def reader_context(gateway, reader_instance):
                def decorator(func):
                    def wrapper(*args, **kwargs):
                        return func(gateway, reader_instance, *args, **kwargs)
                    return wrapper
                return decorator
            
            @reader_context(gateway, reader_instance)
            def on_badge(gateway, reader_instance, badge_uid):
                with Gateways.app.app_context():
                    access_control(gateway, reader_instance, badge_uid)

            threading.Thread(target=gateway.job, args=(reader_instance, on_badge), daemon=True).start()

    @classmethod
    def get(cls, gateway_uid):
        return cls.gateways.get(gateway_uid)