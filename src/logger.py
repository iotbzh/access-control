import io
import logging
import logging.handlers
import threading
import os
import sys
import gzip
import shutil

class ManyLevelsFilter(logging.Filter):

    def __init__(self, levels):
        super().__init__()
        self.levels = levels

    def filter(self, record):
        return record.levelno in self.levels

class Logger:
    log_streams = { }
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    @classmethod
    def init(cls):
        debug_fh = Logger.create_rotating_file_handler("debug")
        debug_fh.setLevel(logging.DEBUG)

        error_fh = Logger.create_rotating_file_handler("errors")
        error_fh.setLevel(logging.ERROR)

        app_fh = Logger.create_rotating_file_handler("app")
        app_fh.setLevel(logging.INFO)
        app_fh.addFilter(ManyLevelsFilter([logging.INFO, logging.WARNING]))
        
        # Add handlers to logging.root to use have rotating log files when using logging.* (like logging.log)
        logging.root.addHandler(debug_fh)
        logging.root.addHandler(error_fh)
        logging.root.addHandler(app_fh)

        # Adding logging handler for uncaught exceptions in main thread and other threads
        sys.excepthook = cls.log_uncaught_exceptions
        threading.excepthook = cls.thread_log_uncaught_exceptions

    @classmethod
    def log_uncaught_exceptions(cls, exc_type, exc_value, exc_traceback, thread=None):
        if issubclass(exc_type, KeyboardInterrupt): # If it's a CTRL+C don't log it
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    @classmethod
    def thread_log_uncaught_exceptions(cls, args):
        return cls.log_uncaught_exceptions(*args)

    @classmethod
    def rotator(cls, source, dest):
        # Compress rotated file
        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)

    @classmethod
    def namer(cls, name):
        return name + ".gz"

    @classmethod
    def get_gateway(cls, uid):
        return logging.getLogger(f"gw-{uid}")
    
    @classmethod
    def get_plugin(cls, uid):
        return logging.getLogger(f"pl-{uid}")
    
    @classmethod
    def get_app(cls, uid):
        return logging.getLogger(f"app-{uid}")

    @classmethod
    def init_logger(cls, type, uid):
        log_stream = io.StringIO()
        cls.log_streams[f"{type}-{uid}"] = log_stream

        stream_handler = logging.StreamHandler(log_stream)
        stream_handler.setFormatter(cls.formatter)
        stream_handler.setLevel(logging.DEBUG)

        file_handler = cls.create_rotating_file_handler(f"{type}-{uid}")
        file_handler.setLevel(logging.DEBUG)

        gw_logger = logging.getLogger(f"{type}-{uid}")
        gw_logger.setLevel(logging.DEBUG)
        
        gw_logger.addHandler(stream_handler)
        gw_logger.addHandler(file_handler)

    @classmethod
    def init_gateway(cls, uid):
        cls.init_logger("gw", uid)

    @classmethod
    def init_plugin(cls, uid):
        cls.init_logger("pl", uid)
    
    @classmethod
    def init_app(cls, uid):
        cls.init_logger("app", uid)
    
    @classmethod
    def create_rotating_file_handler(cls, name):
        # Create a rotation log handler that will rotate each Sunday and will keep them for 156 weeks (almost 3 years)
        fh = logging.handlers.TimedRotatingFileHandler(f'logs/{name}.log', "D", interval=1, backupCount=156)  # TODO: Change D to W6, this is for the tests
        fh.setFormatter(cls.formatter)
        # Use custom rotator and namer to get compressed rotated files
        fh.rotator = cls.rotator
        fh.namer = cls.namer
        return fh