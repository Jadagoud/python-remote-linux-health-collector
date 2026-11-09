import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger():

    log_directory = Path("logs")
    log_directory.mkdir(parents=True, exist_ok=True)

    log_file = log_directory / "health_collector.log"

    logger = logging.getLogger("health_collector")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers.
    if logger.handlers:
        return logger

    # Write logs to a rotating file.
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )

    # Display logs in the terminal.
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
