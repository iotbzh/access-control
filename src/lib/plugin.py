from src.configs import Configs
from src.logger import Logger

class BasePlugin:
    uid = "unknown"
    navlinks = {}
    admin_navlinks = {}

    class Config:
        pass

    @classmethod
    def get_var(cls, var):
        return Configs.get_plugin_var(cls.uid, var)

    @classmethod
    def logger(cls):
        return Logger.get_plugin(cls.uid)