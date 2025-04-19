# utils/logging_core.py
import logging
import os
import datetime
from logging.handlers import RotatingFileHandler
from core.config_core import Config

# Initialize the configuration
config = Config()
log_directory = config.get("Logs", "path", default="./logs")
max_log_files = config.getint("Logs", "max_files", default=10)

def setup_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with the specified name.

    Args:
        name (str): Name of the logger (usually the name of the calling module).

    Returns:
        logging.Logger: Configured logger instance.
    """

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f'{log_directory}/{current_time}.log'

    file_handler = RotatingFileHandler(
        log_file_name, maxBytes=5 * 1024 * 1024, encoding='utf-8', backupCount=config.getint("Logs", "max_files", default=10)
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[file_handler, stream_handler],
    )

    try:
        stream_handler.setStream(open(stream_handler.stream.fileno(), mode='w', encoding='utf-8', closefd=False))
    except Exception as e:

        logging.warning(f"Could not explicitly set UTF-8 encoding on StreamHandler: {e}")

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
        logging.warning(f"Log directory does not exist: {log_dir}")
        return

    if logger is None:
        logging.error("Logger object is None in cleanup_old_logs. Initialization failed.")
        return

    files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not files:
        logger.info("No log files found to clean up.")
        return

    try:
        files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
    except FileNotFoundError:
        logger.warning(f"A log file was deleted during cleanup process in {log_dir}. Retrying might be needed.")
        return

    files_to_remove = files[:-max_files] if max_files > 0 else files  # Remove todos se max_files for 0 ou menos

    if not files_to_remove:
        logger.info("No old log files to remove.")
        return

    logger.info(f"Starting cleanup of old log files in {log_dir}. Keeping last {max_files} files.")
    for f in files_to_remove:
        file_path = os.path.join(log_dir, f)
        try:
            os.remove(file_path)
            logger.info(f"Removed old log file: {file_path}")
        except OSError as e:
            logger.error(f"Failed to remove log file {file_path}: {e}")


if log_directory and isinstance(max_log_files, int):
    cleanup_old_logs(log_dir=log_directory, max_files=max_log_files)
else:
    logging.error("Log directory or max_files configuration is invalid. Skipping log cleanup.")
