#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль логирования для ADB Блюстакс Автоматизация.
Обеспечивает настройку и управление логированием событий программы.
"""

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional, Union
import colorama

# Инициализация colorama для цветного вывода
colorama.init()

# Константы для цветов
COLORS = {
    'DEBUG': colorama.Fore.BLUE,
    'INFO': colorama.Fore.GREEN,
    'WARNING': colorama.Fore.YELLOW,
    'ERROR': colorama.Fore.RED,
    'CRITICAL': colorama.Fore.MAGENTA,
    'RESET': colorama.Fore.RESET
}


class ColoredFormatter(logging.Formatter):
    """Форматирование логов с цветным выводом для консоли."""
    
    def __init__(self, fmt: str) -> None:
        super().__init__(fmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует запись лога с цветом в зависимости от уровня лога.
        
        Args:
            record: Запись лога.
            
        Returns:
            str: Отформатированная строка лога с цветом.
        """
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logger(
    level: str = 'INFO',
    directory: str = 'logs',
    file_format: str = '{date}.log',
    colored: bool = True,
    max_size: int = 10 * 1024 * 1024,  # 10 МБ
    backup_count: int = 5
) -> logging.Logger:
    """
    Настройка логгера с возможностью записи в файл и вывода в консоль.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        directory: Директория для хранения файлов логов.
        file_format: Формат имени файла лога (может содержать {date}).
        colored: Использовать ли цветной вывод в консоль.
        max_size: Максимальный размер файла лога перед ротацией.
        backup_count: Количество файлов лога для ротации.
        
    Returns:
        logging.Logger: Настроенный логгер.
    """
    # Создание директории для логов, если она не существует
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Получение корневого логгера
    logger = logging.getLogger()
    
    # Очистка существующих обработчиков
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Установка уровня логирования
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    logger.setLevel(numeric_level)
    
    # Форматирование логов
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    if colored:
        console_formatter = ColoredFormatter(log_format)
    else:
        console_formatter = logging.Formatter(log_format, date_format)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для файла
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    file_name = file_format.replace('{date}', date_str)
    file_path = os.path.join(directory, file_name)
    
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_device_logger(
    device_id: str,
    base_logger: logging.Logger,
    directory: str = 'logs',
    file_format: str = '{date}_{device}.log',
    max_size: int = 10 * 1024 * 1024,  # 10 МБ
    backup_count: int = 5
) -> logging.Logger:
    """
    Создает отдельный логгер для конкретного устройства.
    
    Args:
        device_id: Идентификатор устройства.
        base_logger: Базовый логгер.
        directory: Директория для хранения файлов логов.
        file_format: Формат имени файла лога.
        max_size: Максимальный размер файла лога перед ротацией.
        backup_count: Количество файлов лога для ротации.
        
    Returns:
        logging.Logger: Настроенный логгер для устройства.
    """
    # Создание директории для логов, если она не существует
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Создание логгера для устройства
    logger_name = f"device_{device_id.replace(':', '_')}"
    device_logger = logging.getLogger(logger_name)
    
    # Очистка существующих обработчиков
    for handler in device_logger.handlers[:]:
        device_logger.removeHandler(handler)
    
    # Установка уровня логирования
    device_logger.setLevel(base_logger.level)
    
    # Форматирование логов
    log_format = f'%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Устройство будет также логировать в консоль через базовый логгер
    device_logger.propagate = True
    
    # Обработчик для файла
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    safe_device_id = device_id.replace(':', '_').replace('.', '_')
    file_name = file_format.replace('{date}', date_str).replace('{device}', safe_device_id)
    file_path = os.path.join(directory, file_name)
    
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(device_logger.level)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    device_logger.addHandler(file_handler)
    
    return device_logger