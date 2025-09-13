import logging
from config import Config


# настройка логирования: в файл или в консоль
def setup_logging():
    log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # очистить существующие handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if Config.DEV_OR_PROD == 'PROD':
        # логирование в файл
        file_handler = logging.FileHandler(
            Config.LOG_FILE,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        print(f"Логи записываются в файл: {Config.LOG_FILE}")
    else:
        # логирование в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        print("Логи выводятся в консоль")

    # Уменьшаем логирование внешних библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Логирование настроено. Уровень: {Config.LOG_LEVEL}")
    logger.info(f"Режим: {'Файл' if Config.LOG_TO_FILE else 'Консоль'}")
