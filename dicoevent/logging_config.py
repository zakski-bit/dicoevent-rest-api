import sys
from pathlib import Path
from loguru import logger

# Base directory for log files
BASE_DIR = Path(__file__).resolve().parent.parent

# Log format strictly matching rubric:
# Example: 2025-06-08 14:41:43.260 | INFO | reservations.views:post:31 - Reservation ... created by ...
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"

def setup_logging():
    """
    Configures Loguru handlers:
    1. application.log: Records INFO level logs with 1-day rotation.
    2. error.log: Records ERROR level logs with 1-day rotation.
    3. sys.stdout: Standard output for console visibility.
    """
    # Remove default handler
    logger.remove()

    # Standard console output
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level="INFO",
        colorize=True
    )

    # application.log (INFO level and above, rotated daily)
    app_log_path = BASE_DIR / "application.log"
    logger.add(
        str(app_log_path),
        format=LOG_FORMAT,
        level="INFO",
        rotation="1 day",
        retention="30 days",
        encoding="utf-8",
        enqueue=True
    )

    # error.log (ERROR level and above, rotated daily)
    error_log_path = BASE_DIR / "error.log"
    logger.add(
        str(error_log_path),
        format=LOG_FORMAT,
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        encoding="utf-8",
        enqueue=True
    )

    return logger

# Initialize logger on import
log = setup_logging()
