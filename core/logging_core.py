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
        log_file_name, maxBytes=5 * 1024 * 1024, backupCount=config.get_max_backups(), encoding='utf-8'
        # Adicionado encoding='utf-8' para o arquivo também
    )
    # Especificar encoding='utf-8' diretamente no StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))
    # Remover a linha que reabre o stream; a codificação padrão do stream pode ser tratada pelo Python ou pelo handler
    # stream_handler.stream = open(stream_handler.stream.fileno(), mode='w', encoding='utf-8', closefd=False) # Linha removida/comentada

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[file_handler, stream_handler],
        # Adicionar encoding='utf-8' aqui também pode ajudar, dependendo da versão do Python
        # encoding='utf-8' # Descomente se necessário (Python 3.9+)
    )

    # Configurar encoding para o stream_handler especificamente se basicConfig não for suficiente
    try:
        # Tenta definir a codificação do stream handler explicitamente.
        # Em algumas versões/configurações, isso pode ser necessário.
        stream_handler.setStream(open(stream_handler.stream.fileno(), mode='w', encoding='utf-8', closefd=False))
    except Exception as e:
        # Se falhar (ex: stream não tem fileno), loga um aviso mas continua.
        logging.warning(f"Could not explicitly set UTF-8 encoding on StreamHandler: {e}")

    # Retorna a instância do logger configurada
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
        # Usa logging.warning diretamente caso o logger global ainda não esteja totalmente pronto
        # ou se houver algum problema na ordem de execução (embora com o return, deve funcionar)
        logging.warning(f"Log directory does not exist: {log_dir}")
        return

    # Verifica se o logger foi inicializado corretamente antes de usar
    if logger is None:
        logging.error("Logger object is None in cleanup_old_logs. Initialization failed.")
        return

    files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not files:
        logger.info("No log files found to clean up.")
        return

    # Ordena os arquivos por data de modificação (do mais antigo para o mais recente)
    try:
        files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
    except FileNotFoundError:
        logger.warning(f"A log file was deleted during cleanup process in {log_dir}. Retrying might be needed.")
        return  # Ou pode tentar relistar os arquivos

    # Calcula quais arquivos remover (todos exceto os 'max_files' mais recentes)
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
        except OSError as e:  # Usar OSError que é mais geral para erros de remoção de arquivo
            logger.error(f"Failed to remove log file {file_path}: {e}")


# Clean up old logs on startup
# É importante garantir que config.get_path() e config.get_max_files() retornem valores válidos
log_directory = config.get_path()
max_log_files = config.get_max_files()

if log_directory and isinstance(max_log_files, int):
    cleanup_old_logs(log_dir=log_directory, max_files=max_log_files)
else:
    # Usa logging diretamente pois o logger pode não estar pronto ou a config falhou
    logging.error("Log directory or max_files configuration is invalid. Skipping log cleanup.")
