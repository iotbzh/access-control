import importlib
import glob
import os
import threading

from src.models import db, dbs, Gateway, Reader
from src.access import access_control
from src.configs import Configs

class Gateways:

    gateways_folder = "gateways"
    gateways = {}

    @classmethod
    def get_all_gateways(cls):
        for module_file in glob.glob(f"{cls.gateways_folder}/*.py"):
            module_name = os.path.basename(module_file)[:-3]
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
            reader_class = gateway.reader_class

            for reader in readers:
                dbs.expunge(reader)
                reader_instance = reader_class(reader, **reader.gateway_configs)
                gateway.connect(reader_instance)
                
                def on_badge(badge_uid):
                    with app.app_context():
                        access_control(gateway, reader_instance, badge_uid)

                threading.Thread(target=gateway.job, args=(reader_instance, on_badge), daemon=True).start()