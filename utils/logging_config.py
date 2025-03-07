"""
Logging Configuration

This module configures application logging with appropriate handlers and formatters.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logging(log_dir: str = "logs", log_file: str = "discord_summary_bot.log", debug: bool = False) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_dir: Directory to store log files
        log_file: Name of the log file
        debug: Whether to enable debug logging
        
    Returns:
        Root logger instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set log level based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler with rotation
    file_path = os.path.join(log_dir, log_file)
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure library loggers
    # Reduce verbosity of some noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Create and return application logger
    logger = logging.getLogger('discord_summary_bot')
    logger.info("Logging configured")
    if debug:
        logger.info("Debug logging enabled")
    
    return logger