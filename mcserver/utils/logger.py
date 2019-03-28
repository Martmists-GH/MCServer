from logging import DEBUG, getLogger
from typing import Union

log = getLogger("MC-Server")
log.setLevel(DEBUG)


def info(data: Union[str, bytes]):
    log.info(data)


def debug(data: Union[str, bytes]):
    log.debug(data)


def warn(data: Union[str, bytes]):
    log.warning(data)


def error(data: Union[str, bytes]):
    log.error(data)
