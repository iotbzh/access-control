from src.models import db, dbs, Plugin

class Configs:

    # @classmethod
    # def get_default_config(cls, gateway):
    #     configs = gateway.configs
    #     default = {}
    #     for config in configs:
    #         default[config.name] = config.default
    #     return default


    @classmethod
    def get_default_config(cls, configs):
        default = {}
        print(configs.__annotations__)
        for config in configs.__annotations__:
            default[config] = getattr(configs, config, None)
        return default
    
    @classmethod
    def get_plugin_var(cls, plugin_uid, var):
        plugin = dbs.execute(db.select(Plugin).where(Plugin.uid == plugin_uid)).scalar_one_or_none()
        return plugin.configs.get(var)