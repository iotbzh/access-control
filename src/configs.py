from src.models import db, dbs, Plugin, Gateway

class Configs:

    @staticmethod
    def get_default_config(configs):
        default = {}
        for config in configs.__annotations__:
            default[config] = getattr(configs, config, None)
        return default
    
    @staticmethod
    def get_plugin_var(plugin_uid, var):
        plugin = dbs.execute(db.select(Plugin).where(Plugin.uid == plugin_uid)).scalar_one_or_none()
        if not plugin: return None
        return plugin.configs.get(var)
    
    @staticmethod
    def get_gateway_var(gateway_uid, var):
        gateway = dbs.execute(db.select(Gateway).where(Gateway.uid == gateway_uid)).scalar_one_or_none()
        if not gateway: return None
        return gateway.configs.get(var)