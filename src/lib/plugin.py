from src.configs import Configs

class BasePlugin:
    uid = "unknown"
    navlinks = {}

    class Config:
        pass

    @classmethod
    def get_var(cls, var):
        return Configs.get_plugin_var(cls.uid, var)