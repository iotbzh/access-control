class Action:

    def __new__(self):
        return self.decorate()
    
    @classmethod
    def decorate(self):
        def decorator(func):
            def wraps(*args, **kwargs):
                return func(*args, **kwargs)
            self.set_func_attr(wraps)
            wraps.is_action = True
            wraps.__name__ = func.__name__
            return wraps
        return decorator

    @classmethod
    def set_func_attr(self, func): pass

class ActionButton(Action):

    def __new__(self, name, admin = True):
        self.name = name
        self.admin = admin
        return self.decorate()
    
    @classmethod
    def set_func_attr(self, func):
        func.is_button_action = True
        func.name = self.name
        func.admin = self.admin