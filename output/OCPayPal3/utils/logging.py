import logging
import os
from datetime import datetime

from ..loader import prefix_folder


def setup_logging():
    # Создание директорий для логов
    error_log_dir = f"{prefix_folder}logs/errors"
    debug_log_dir = f"{prefix_folder}logs/debug"

    if not os.path.exists(error_log_dir):
        os.makedirs(error_log_dir)
    if not os.path.exists(debug_log_dir):
        os.makedirs(debug_log_dir)

    # Форматирование текущего времени для имен файлов логов
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Создание файлов для логов ошибок и отладочных сообщений
    error_log_file = os.path.join(error_log_dir, f"log_{current_time}.log")
    debug_log_file = os.path.join(debug_log_dir, f"log_{current_time}.log")

    # Настройка логгера для ошибок
    error_handler = logging.FileHandler(error_log_file, 'a', 'utf-8')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    error_handler.setFormatter(error_formatter)

    # Настройка логгера для отладочных сообщений
    debug_handler = logging.FileHandler(debug_log_file, 'a', 'utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter('%(asctime)s %(message)s')  # Fixed formatter string
    debug_handler.setFormatter(debug_formatter)

    # Настройка основного логгера
    logging.basicConfig(level=logging.DEBUG, handlers=[error_handler, debug_handler])
