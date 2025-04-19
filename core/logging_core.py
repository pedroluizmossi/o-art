import logging
import os
from logging.handlers import RotatingFileHandler

_loggers = {}


def setup_logger(name: str, config=None) -> logging.Logger:
    """
    Configures and returns a logger with the specified name.
    Avoids reconfiguring if logger already exists.

    Args:
        name (str): Name of the logger (usually the name of the calling module).
        config (Config): Optional Config instance (or dict/object with log settings).

    Returns:
        logging.Logger: Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    if config is None:
        try:
            from core.config_core import Config
            config_instance = Config()
            log_config = {
                'level': config_instance.get('Logs', 'level', 'INFO'),
                'path': config_instance.get('Logs', 'path', './logs'),
                'max_backups': config_instance.getint('Logs', 'max_backups', 5),
                'max_files': config_instance.getint('Logs', 'max_files', 10)  # Para cleanup
            }
        except Exception as e:
            logging.basicConfig(level=logging.WARNING)
            logging.warning(f"Failed to load logging configuration: {e}. Using basic config.", exc_info=True)
            log_config = {'level': 'INFO', 'path': './logs', 'max_backups': 5, 'max_files': 10}
    else:
        log_config = config

    log_dir = log_config.get('path', './logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            logging.basicConfig(level=logging.ERROR)
            logging.error(f"Failed to create log directory {log_dir}: {e}", exc_info=True)
            logger = logging.getLogger(name)
            _loggers[name] = logger
            return logger

    log_level_str = log_config.get('level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file_name = f'{log_dir}/{name}_latest.log'

    file_handler = RotatingFileHandler(
        log_file_name, maxBytes=5 * 1024 * 1024,
        backupCount=log_config.get('max_backups', 5),
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    _loggers[name] = logger
    return logger


def cleanup_old_logs(log_dir: str, max_files: int):
    """
    Removes old log files (matching *.log pattern), keeping only the most recent ones.
    Adds check before removing to mitigate race conditions.
    """
    temp_logger = logging.getLogger(__name__ + ".cleanup")
    if not temp_logger.handlers:
        temp_logger.addHandler(logging.StreamHandler())
        temp_logger.setLevel(logging.INFO)

    if not os.path.exists(log_dir):
        temp_logger.warning(f"Log directory for cleanup does not exist: {log_dir}")
        return

    if not isinstance(max_files, int) or max_files < 0:
        temp_logger.error(f"Invalid max_files for log cleanup: {max_files}. Must be a non-negative integer.")
        return

    try:
        files = [f for f in os.listdir(log_dir) if f.endswith('.log') and os.path.isfile(os.path.join(log_dir, f))]
        if not files:
            temp_logger.info(f"No .log files found in {log_dir} to clean up.")
            return

        files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))

    except Exception as e:
        temp_logger.error(f"Error listing or sorting log files in {log_dir}: {e}", exc_info=True)
        return

    files_to_remove_count = len(files) - max_files
    if files_to_remove_count <= 0:
        temp_logger.info(
            f"Log file count ({len(files)}) is within the limit ({max_files}). No cleanup needed in {log_dir}.")
        return

    files_to_remove = files[:files_to_remove_count]

    temp_logger.info(
        f"Starting cleanup of old log files in {log_dir}. Found {len(files)}, keeping last {max_files}, removing {len(files_to_remove)}.")
    removed_count = 0
    for f in files_to_remove:
        file_path = os.path.join(log_dir, f)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                temp_logger.info(f"Removed old log file: {file_path}")
                removed_count += 1
            else:
                temp_logger.warning(f"Log file vanished before removal (likely race condition): {file_path}")
        except OSError as e:
            temp_logger.error(f"Failed to remove log file {file_path}: {e}")
        except Exception as e:  # Captura outros erros inesperados
            temp_logger.exception(f"Unexpected error removing log file {file_path}: {e}")

    temp_logger.info(f"Log cleanup finished for {log_dir}. Successfully removed {removed_count} file(s).")
