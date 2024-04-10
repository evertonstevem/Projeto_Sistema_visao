import logging
import sys
from typing import NoReturn


class Logger:
    """Class to start the logger."""

    _LOGGER = logging.getLogger("PYTHON")

    def __init__(self, log: str):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
        )
        level = logging._nameToLevel[log]

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(
            level
            if level
            in [
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
            ]
            else logging.WARNING
        )
        stdout_handler.setFormatter(formatter)
        stdout_handler.addFilter(lambda record: record.levelno <= logging.WARNING)
        self._LOGGER.addHandler(stdout_handler)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(level)
        stderr_handler.setFormatter(formatter)
        stderr_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
        self._LOGGER.addHandler(stderr_handler)

        self._LOGGER.setLevel(level)

    @classmethod
    def err_exit(cls, msg: str, code: int) -> NoReturn:
        """Log to stderr and exit - ERROR."""
        cls._LOGGER.error(f"{code} - {msg}")
        sys.exit(code)

    @classmethod
    def info(cls, msg: str) -> None:
        """Log to stdout - INFO."""
        cls._LOGGER.info(msg)

    @classmethod
    def debug(cls, msg: str) -> None:
        """Log to stdout - DEBUG."""
        cls._LOGGER.debug(msg)

    @classmethod
    def warning(cls, msg: str) -> None:
        """Log to stdout - WARNING."""
        cls._LOGGER.warning(msg)

    @classmethod
    def critical(cls, msg: str) -> None:
        """Log to stderr - CRITICAL."""
        cls._LOGGER.critical(msg)
