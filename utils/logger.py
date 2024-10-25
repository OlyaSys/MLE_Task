import logging


def get_root_logger(service_name: str) -> logging.Logger:
    """
    Generate logger

    :rtype logging.Logger
    """
    logger: logging.Logger = logging.getLogger(service_name)
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] - %(message)s")
    )
    logger.addHandler(_console_handler)
    logger.setLevel(logging.DEBUG)
    return logger

LOGGER: logging.Logger = get_root_logger('invest-portfolio')
