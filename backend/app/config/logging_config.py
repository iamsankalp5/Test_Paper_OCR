"""
Centralized logging configuration with file and console handlers.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from app.config.settings import settings


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_template = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_template + reset,
        logging.INFO: blue + format_template + reset,
        logging.WARNING: yellow + format_template + reset,
        logging.ERROR: red + format_template + reset,
        logging.CRITICAL: bold_red + format_template + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging():
    """
    Setup logging configuration with both file and console handlers.
    Creates logs directory if it doesn't exist.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (10MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info(f"Logging initialized at {datetime.now()}")
    root_logger.info(f"Log Level: {settings.log_level}")
    root_logger.info(f"Log File: {settings.log_file}")
    root_logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)