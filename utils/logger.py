from loguru import logger
import sys
import os
from datetime import datetime

def setup_logger():
    """
    Set up Loguru logger with console and file handlers.
    """
    os.makedirs("logs", exist_ok=True)

    # Remove default logger handler to avoid duplicate logs
    logger.remove()

    # Console
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>[{time:HH:mm:ss}]</green> <level>{level}</level> | <cyan>{message}</cyan>"
    )

    # File (rotating daily)
    logger.add(
        f"logs/posteract_{datetime.now().strftime('%Y-%m-%d')}.log",
        rotation="10 MB",      # or "1 day", "1 week"
        retention="10 days",   # delete old logs after 10 days
        level="DEBUG",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}"
    )

    logger.info("✅ Logging initialized with Loguru")

def get_logger(name=None):
    """
    Get the configured Loguru logger.
    """
    return logger
