from src.configs import Configs

class BaseGateway:
    uid = "unknown"
    name = "Unknown"
    reader_class = None
    readers = {}

    class Config:
        pass

    class Actions:
        pass

    @staticmethod
    def connect(reader):
        pass

    @staticmethod
    def disconnect(reader):
        pass

    @classmethod
    def restart(cls, reader):
        cls.disconnect(reader)
        cls.connect(reader)

    @staticmethod
    def job(reader, on_badge):
        pass

    @staticmethod
    def event(reader, authorized, badge_uid):
        pass
    
    @classmethod
    def get_all_actions(cls):
        actions = []
        for method in dir(cls.Actions):
            if hasattr(getattr(cls.Actions, method), "is_action"):
                actions.append(getattr(cls.Actions, method)) 
        return actions

    @classmethod
    def get_action(cls, name):
        for method in dir(cls.Actions):
            action = getattr(cls.Actions, method)
            if hasattr(action,  "__name__") and action.__name__ == name:
                return action
        return None
    
    @classmethod
    def get_reader_instance(cls, reader_id):
        return cls.readers.get(int(reader_id))

    @classmethod
    def get_var(cls, var):
        return Configs.get_gateway_var(cls.uid, var)