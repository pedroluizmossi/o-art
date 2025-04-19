import logging
import os
from logging.handlers import RotatingFileHandler

_loggers = {}


def setup_logger(name: str, config=None) -> logging.Logger:
    """
    Configura e retorna um logger com o nome especificado.
    Evita reconfiguração se já existir logger com esse nome.

    Args:
        name (str): Nome do logger (normalmente o nome do módulo chamador).
        config (Config): Instância opcional de Config (ou dict/obj com configurações de log).

    Returns:
        logging.Logger: Instância configurada do logger.
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
            logging.warning(
                "Failed to load logging configuration: %s. Using basic config.", e,
                exc_info=True
            )
            log_config = {'level': 'INFO', 'path': './logs', 'max_backups': 5, 'max_files': 10}
    else:
        log_config = config

    log_dir = log_config.get('path', './logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            logging.basicConfig(level=logging.ERROR)
            logging.error(
                "Failed to create log directory %s: %s", log_dir, e,
                exc_info=True
            )
            logger = logging.getLogger(name)
            _loggers[name] = logger
            return logger

    log_level_str = log_config.get('level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file_name = '{}/{}_latest.log'.format(log_dir, name)

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
