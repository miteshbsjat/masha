import logging
import logging.config
from sys import stdin
from pathlib import Path


def create_logger(name):
    log_conf_file = Path(__file__).parent / "logging.conf"
    logging.config.fileConfig(log_conf_file)
    return logging.getLogger(name)
