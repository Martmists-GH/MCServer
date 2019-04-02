# Stdlib
from logging import DEBUG, getLogger, basicConfig
from typing import Union

basicConfig(level=DEBUG)
log = getLogger("MC-Server")
log.setLevel(DEBUG)
log.info("Logger ready")


def info(data: Union[str, bytes]):
    log.info(data)


def debug(data: Union[str, bytes]):
    log.error(data)


def warn(data: Union[str, bytes]):
    log.warning(data)


def error(data: Union[str, bytes]):
    log.error(data)
