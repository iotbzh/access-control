from src.configs import Configs

class BasePlugin:
    uid = "unknown"

    class Config:
        pass

    @classmethod
    def get_var(cls, var):
        return Configs.get_plugin_var(cls.uid, var)