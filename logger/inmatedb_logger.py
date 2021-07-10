if __name__ == "__main__":
    import os, sys
    # Add path for main files to run test script.
    sys.path.append(os.path.realpath("."))

import sys

import logging
import textwrap
from functools import partial

from metaclasses.singleton import Singleton

from logger.push_handler import PushHandler, PushCredentials
from logging.handlers import RotatingFileHandler


class LevelFilter(logging.Filter):
    def __init__(self, low, high=None):
        super(LevelFilter, self).__init__()
        self._low = low
        self._high = low if high is None else high
    
    def filter(self, record):
        return self._low <= record.levelno <= self._high

class InatedbLogger(metaclass=Singleton):

    def __init__(self, log_level=logging.DEBUG, push_credentials=None):
        message_fmt = textwrap.dedent('''

        {asctime}
        {levelname}: {module}.{funcName} (line {lineno})
        msg: {message}\
        ''')
        date_fmt = "%m/%d/%Y %I:%M:%S %p"

        logging.getLogger('urllib3.connectionpool').addFilter(lambda r: False)
        self.__logger = logging.getLogger("inmatedb_log")

        handlers = []
        if log_level == logging.DEBUG:
            self.debug_log = logging.StreamHandler()
            self.debug_log.setLevel(logging.DEBUG)
            # self.debug_log.addFilter(LevelFilter(logging.DEBUG, logging.CRITICAL))
            handlers.append(self.debug_log)

        self.info_log = RotatingFileHandler("logs/inmatedb_info.log", maxBytes=2000, backupCount=3)
        self.info_log.addFilter(LevelFilter(logging.INFO, logging.WARNING))
        handlers.append(self.info_log)

        self.error_log = RotatingFileHandler("logs/inmatedb_error.log", maxBytes=2000, backupCount=3)
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
            

if __name__ == "__main__":

    ## In case you want to recieve notifications on your phone/desktop I added logging support for PushBullet
    # credentials = PushCredentials(
    #     api_key="YOUR_API_KEY",
    #     channel_tag="CHANNEL_TAG"
    # )
    # logger = InatedbLogger(push_credentials=credentials)

    logger = InatedbLogger(log_level=logging.DEBUG)

    def anything_that_breaks():
        logger.info("running function to test logger.")

        try:
            logger.debug("about to do something really dangerous...")
            1/0
            logger.warning("uh... we shouldn't get this far.")
        except ZeroDivisionError:
            logger.error("can't divide by zero.")
            logger.critical("critical failure.")
    
    anything_that_breaks()
