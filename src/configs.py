from src.models import db, dbs, Plugin, Gateway

class Configs:

    @classmethod
    def get_default_config(cls, configs):
        default = {}
        for config in configs.__annotations__:
            default[config] = getattr(configs, config, None)
        return default
    
    @classmethod
    def get_plugin_var(cls, plugin_uid, var):
        plugin = dbs.execute(db.select(Plugin).where(Plugin.uid == plugin_uid)).scalar_one_or_none()
        return plugin.configs.get(var)
    
    @classmethod
    def get_gateway_var(cls, gateway_uid, var):
        gateway = dbs.execute(db.select(Gateway).where(Gateway.uid == gateway_uid)).scalar_one_or_none()
        return gateway.configs.get(var)