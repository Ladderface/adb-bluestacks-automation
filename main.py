#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ADB Блюстакс Автоматизация
Многопоточный и асинхронный инструмент для автоматизации работы с Android-эмуляторами BlueStacks 5
через протокол ADB с гибкой системой конфигурации.

Автор: Claude 3.7 Sonnet
Версия: 1.0.0
"""

import os
import sys
import time
import asyncio
import logging
import argparse
import yaml
import importlib.util
from typing import Dict, List, Any, Optional, Tuple

# Добавление пути к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Импорт модулей проекта
from modules.logger import setup_logger
from modules.console_ui import ConsoleUI
from modules.adb_manager import ADBManager
from modules.device_manager import DeviceManager
from modules.scheduler import Scheduler
from modules.config_loader import ConfigLoader

# Глобальные переменные
CONFIG_PATH = 'config.yaml'
VERSION = '1.0.0'


class ADBAutomation:
    """
    Основной класс программы для автоматизации работы с ADB и BlueStacks.
    Координирует все компоненты системы и управляет жизненным циклом приложения.
    """

    def __init__(self):
        """Инициализация основного класса программы."""
        self.config = {}
        self.logger = None
        self.ui = None
        self.adb_manager = None
        self.device_manager = None
        self.scheduler = None
        self.config_loader = None
        self.running = False
        self.loaded_configs = {}

    async def initialize(self) -> bool:
        """
        Инициализация компонентов программы и загрузка конфигурации.
        
        Returns:
            bool: Успешна ли инициализация.
        """
        try:
            # Загрузка конфигурации
            if not os.path.exists(CONFIG_PATH):
                print(f"[ОШИБКА] Файл конфигурации не найден: {CONFIG_PATH}")
                return False
                
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # Настройка логгера
            log_config = self.config.get('logging', {})
            self.logger = setup_logger(
                level=log_config.get('level', 'INFO'),
                directory=log_config.get('directory', 'logs'),
                colored=log_config.get('colored_console', True)
            )
            
            # Создание необходимых директорий
            self._create_directories()
            
            # Инициализация пользовательского интерфейса
            self.ui = ConsoleUI(self.config.get('ui', {}), self.logger)
            
            # Инициализация менеджера ADB
            self.adb_manager = ADBManager(self.config.get('adb', {}), self.logger, self.ui)
            
            # Проверка доступности ADB
            if not await self.adb_manager.initialize():
                self.logger.error("Не удалось инициализировать ADB. Проверьте установку ADB или пути в конфигурации.")
                return False
            
            # Инициализация менеджера устройств
            self.device_manager = DeviceManager(
                self.config.get('devices', {}),
                self.adb_manager,
                self.logger,
                self.ui
            )
            
            # Загрузка списка устройств
            if not await self.device_manager.load_devices():
                self.logger.warning("Не удалось загрузить список устройств или список пуст.")
            
            # Инициализация загрузчика конфигураций
            self.config_loader = ConfigLoader(
                self.config.get('directories', {}).get('configs', 'configs'),
                self.logger
            )
            
            # Инициализация планировщика
            self.scheduler = Scheduler(
                self.config.get('scheduler', {}),
                self.device_manager,
                self.config_loader,
                self.logger,
                self.ui
            )
            
            # Вывод информации о запуске
            self.ui.print_header(f"ADB Блюстакс Автоматизация v{VERSION}")
            self.ui.print_info(f"Загружено {len(self.device_manager.devices)} устройств")
            
            # Все компоненты успешно инициализированы
            self.running = True
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"Ошибка при инициализации: {e}")
            else:
                print(f"[КРИТИЧЕСКАЯ ОШИБКА] Ошибка при инициализации: {e}")
            return False

    def _create_directories(self) -> None:
        """Создание необходимых директорий для работы программы."""
        directories = self.config.get('directories', {})
        for key, directory in directories.items():
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                self.logger.debug(f"Создана директория: {directory}")

    async def start(self) -> None:
        """Запуск основного цикла программы."""
        if not self.running:
            self.logger.error("Программа не была правильно инициализирована.")
            return

        try:
            # Запуск планировщика
            if self.config.get('scheduler', {}).get('enabled', True):
                await self.scheduler.start()
                
            # Если настроен немедленный запуск
            if self.config.get('scheduler', {}).get('run_on_start', True):
                self.ui.print_info("Запуск автоматизации...")
                await self.scheduler.run_automation()
            
            # Запуск интерфейса командной строки
            await self.ui.start_cli(self)
            
        except KeyboardInterrupt:
            self.ui.print_info("Получен сигнал завершения программы (Ctrl+C)")
        except Exception as e:
            self.logger.exception(f"Ошибка в основном цикле программы: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Корректное завершение работы программы."""
        self.ui.print_info("Завершение работы программы...")
        
        # Остановка планировщика
        if self.scheduler:
            await self.scheduler.stop()
        
        # Отключение от устройств
        if self.device_manager:
            await self.device_manager.disconnect_all()
        
        # Остановка ADB сервера
        if self.adb_manager:
            await self.adb_manager.stop_server()
        
        self.ui.print_info("Программа успешно завершена.")
        self.running = False

    async def reload_config(self) -> bool:
        """
        Перезагрузка конфигурации без перезапуска программы.
        
        Returns:
            bool: Успешна ли перезагрузка.
        """
        try:
            self.ui.print_info("Перезагрузка конфигурации...")
            
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                new_config = yaml.safe_load(f)
            
            # Обновление конфигурации компонентов
            self.config = new_config
            
            # Обновление конфигурации логгера
            log_config = self.config.get('logging', {})
            logging.getLogger().setLevel(log_config.get('level', 'INFO'))
            
            # Обновление UI
            self.ui.update_config(self.config.get('ui', {}))
            
            # Обновление ADB менеджера
            self.adb_manager.update_config(self.config.get('adb', {}))
            
            # Обновление менеджера устройств
            self.device_manager.update_config(self.config.get('devices', {}))
            
            # Обновление планировщика
            self.scheduler.update_config(self.config.get('scheduler', {}))
            
            self.ui.print_success("Конфигурация успешно перезагружена.")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при перезагрузке конфигурации: {e}")
            self.ui.print_error(f"Не удалось перезагрузить конфигурацию: {e}")
            return False

    def parse_command_line(self) -> argparse.Namespace:
        """
        Разбор аргументов командной строки.
        
        Returns:
            argparse.Namespace: Разобранные аргументы.
        """
        parser = argparse.ArgumentParser(description='ADB Блюстакс Автоматизация')
        parser.add_argument('--config', '-c', type=str, default=CONFIG_PATH,
                          help='Путь к конфигурационному файлу')
        parser.add_argument('--run', '-r', type=str, default=None,
                          help='Запустить конкретный конфиг сразу после запуска')
        parser.add_argument('--debug', '-d', action='store_true',
                          help='Включить режим отладки')
        return parser.parse_args()


async def main():
    """Основная точка входа в программу."""
    app = ADBAutomation()
    
    # Разбор аргументов командной строки
    args = app.parse_command_line()
    
    # Установка пути к конфигурации
    global CONFIG_PATH
    CONFIG_PATH = args.config
    
    # Инициализация программы
    if not await app.initialize():
        print("[КРИТИЧЕСКАЯ ОШИБКА] Не удалось инициализировать программу. Выход.")
        return 1
    
    # Запуск конкретного конфига, если указан
    if args.run:
        app.ui.print_info(f"Запуск конфига {args.run}...")
        await app.scheduler.run_specific_config(args.run)
    
    # Запуск основного цикла программы
    await app.start()
    return 0


if __name__ == "__main__":
    # Запуск асинхронной программы
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА] {e}")
        sys.exit(1)