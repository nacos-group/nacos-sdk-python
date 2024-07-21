import logging
from logging import handlers
from datetime import timedelta

class NacosLogger:
    def __init__(self, logger):
        self.logger = logger

    def info(self, *args):
        self.logger.info(*args)

    def warn(self, *args):
        self.logger.warning(*args)

    def error(self, *args):
        self.logger.error(*args)

    def debug(self, *args):
        self.logger.debug(*args)

    def infof(self, fmt, *args):
        self.logger.info(fmt, *args)

    def warnf(self, fmt, *args):
        self.logger.warning(fmt, *args)

    def errorf(self, fmt, *args):
        self.logger.error(fmt, *args)

    def debugf(self, fmt, *args):
        self.logger.debug(fmt, *args)


class Config:
    def __init__(self, level="info", sampling=None, append_to_stdout=False, log_rolling_config=None):
        self.level = level
        self.sampling = sampling
        self.append_to_stdout = append_to_stdout
        self.log_rolling_config = log_rolling_config


def get_log_level(level_str):
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }
    return levels.get(level_str.lower(), logging.INFO)


def build_logger_config(client_config):
    logger_config = Config(
        level=client_config.log_level,
        append_to_stdout=client_config.append_to_stdout,
    )
    
    if client_config.log_sampling:
        logger_config.sampling = client_config.log_sampling

    if client_config.log_rolling_config:
        logger_config.log_rolling_config = client_config.log_rolling_config

    return logger_config


def init_logger(config):
    log_level = get_log_level(config.level)
    handler = get_log_writer(config.log_rolling_config)
    
    if config.append_to_stdout:
        handler.addFilter(logging.Filter(name="stdout"))

    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    return NacosLogger(logger)


def get_log_writer(rolling_config):
    if rolling_config:
        handler = handlers.TimedRotatingFileHandler(
            filename=rolling_config.filename,
            when="midnight",
            interval=1,
            backupCount=rolling_config.max_backups,
            encoding="utf8",
        )
        
        if rolling_config.compress:
            handler.suffix = "%Y%m%d%H%M%S.gz"
            handler.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        else:
            handler.suffix = "%Y%m%d%H%M%S"
            handler.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        
        return handler
    else:
        handler = logging.FileHandler(filename="nacos.log", encoding="utf8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        return handler