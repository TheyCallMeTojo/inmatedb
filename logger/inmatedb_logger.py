import os, sys

import sys

import logging
import textwrap
from functools import partial

from metaclasses.singleton import Singleton

from logger.push_handler import PushHandler, PushCredentials
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from helpers.pathutils import get_project_dir, extend_relpath


class LevelFilter(logging.Filter):
    def __init__(self, low, high=None):
        super(LevelFilter, self).__init__()
        self._low = low
        self._high = low if high is None else high
    
    def filter(self, record):
        return self._low <= record.levelno <= self._high

class InmatedbLogger(metaclass=Singleton):

    def __init__(self, log_level=logging.DEBUG, push_credentials=None):
        message_fmt = textwrap.dedent('''
        {asctime}
        {levelname}: {module}.{funcName} (line {lineno})
        msg: {message}
        ''')
        date_fmt = "%m/%d/%Y %I:%M:%S %p"

        logging.getLogger('urllib3.connectionpool').addFilter(lambda r: False)
        logging.getLogger('urllib3.util.retry').addFilter(lambda r: False)
        
        
        self.__logger = logging.getLogger("inmatedb_log")

        handlers = []
        if log_level == logging.DEBUG:
            self.debug_log = logging.StreamHandler()
            self.debug_log.setLevel(logging.DEBUG)
            # self.debug_log.addFilter(LevelFilter(logging.DEBUG, logging.CRITICAL))
            handlers.append(self.debug_log)

        logs_folderpath = extend_relpath("logs")
        if not os.path.exists(logs_folderpath):
            os.makedirs(logs_folderpath)
        
        info_log_path = extend_relpath("logs/inmatedb_info.log")
        self.info_log = TimedRotatingFileHandler(info_log_path, when="h", interval=1, backupCount=3)
        self.info_log.addFilter(LevelFilter(logging.INFO, logging.WARNING))
        handlers.append(self.info_log)

        error_log_path = extend_relpath("logs/inmatedb_error.log")
        self.error_log = RotatingFileHandler(error_log_path, maxBytes=5000, backupCount=5)
        self.error_log.addFilter(LevelFilter(logging.ERROR, logging.CRITICAL))
        handlers.append(self.error_log)

        if push_credentials is not None:
            self.push_handler = PushHandler(push_credentials)
            self.push_handler.addFilter(LevelFilter(logging.ERROR, logging.CRITICAL))
            handlers.append(self.push_handler)
        
        logging.basicConfig(
            level=log_level,
            format=message_fmt,
            datefmt=date_fmt,
            style="{",
            handlers=handlers
        )


    @property
    def debug(self):
        _type, _value, _tb = sys.exc_info()
        return partial(self.__logger.debug, exc_info=_value)

    @property
    def info(self):
        return partial(self.__logger.info)

    @property
    def warning(self):
        _type, _value, _tb = sys.exc_info()
        return partial(self.__logger.warning, exc_info=_value)

    @property
    def error(self):
        _type, _value, _tb = sys.exc_info()
        return partial(self.__logger.error, exc_info=_value)

    @property
    def critical(self):
        _type, _value, _tb = sys.exc_info()
        return partial(self.__logger.critical, exc_info=_value)

