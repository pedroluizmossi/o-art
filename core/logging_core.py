# utils/logging_core.py
import logging
import os
import datetime
from logging.handlers import RotatingFileHandler
from core.config_core import Config

# Initialize the configuration
config = Config()
config = config.Logs(config)

def setup_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with the specified name.

    Args:
        name (str): Name of the logger (usually the name of the calling module).

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_dir = config.get_path()
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f'{log_dir}/{current_time}.log'

    # Configure handlers
    file_handler = RotatingFileHandler(
        log_file_name, maxBytes=5 * 1024 * 1024, backupCount=config.get_max_backups()
    )
    stream_handler = logging.StreamHandler()

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[file_handler, stream_handler]
    )

    return logging.getLogger(name)

logger = setup_logger(__name__)

def cleanup_old_logs(log_dir: str, max_files: int = 10) -> None:
    """
    Removes old log files, keeping only the most recent ones.

    Args:
        log_dir (str): Directory where the log files are stored.
        max_files (int): Maximum number of log files to keep.
    """
    if not os.path.exists(log_dir):
        logger.warning(f"Log directory does not exist: {log_dir}")
        return

    files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not files:
        logger.info("No log files found to clean up.")
        return

    files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
    files_to_remove = files[:-max_files]
    if not files_to_remove:
        logger.info("No old log files to remove.")
        return

    for f in files_to_remove:
        file_path = os.path.join(log_dir, f)
        try:
            os.remove(file_path)
            logger.info(f"Removed log file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to remove log file {file_path}: {e}")

# Clean up old logs on startup
cleanup_old_logs(log_dir=config.get_path(), max_files=config.get_max_files())