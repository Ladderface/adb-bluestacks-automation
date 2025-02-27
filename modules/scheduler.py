#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль планировщика для ADB Блюстакс Автоматизация.
Обеспечивает запуск автоматизации по расписанию и управление выполнением конфигураций.
"""

import os
import time
import asyncio
import logging
import schedule
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
import importlib

from modules.action_executor import ActionExecutor


class Scheduler:
    """
    Класс планировщика для управления запуском автоматизации по расписанию.
    """

    def __init__(
        self, 
        config: Dict[str, Any], 
        device_manager, 
        config_loader, 
        logger: logging.Logger, 
        ui
    ):
        """
        Инициализация планировщика.
        
        Args:
            config: Конфигурация планировщика.
            device_manager: Экземпляр менеджера устройств.
            config_loader: Экземпляр загрузчика конфигураций.
            logger: Логгер для записи событий.
            ui: Интерфейс пользователя для вывода информации.
        """
        self.config = config
        self.device_manager = device_manager
        self.config_loader = config_loader
        self.logger = logger
        self.ui = ui
        
        # Включение автоматического запуска по расписанию
        self.enabled = config.get('enabled', True)
        
        # Минуты для запуска (каждый час)
        self.run_minutes = config.get('run_minutes', [5, 25, 45])
        
        # Максимальное количество одновременно запущенных потоков
        self.max_threads = config.get('max_threads', 20)
        
        # Запуск немедленно после старта программы
        self.run_on_start = config.get('run_on_start', True)
        
        # Состояние планировщика
        self.running = False
        self.paused = False
        
        # Процессор действий
        self.executor = None
        
        # Задача планировщика
        self.scheduler_task = None
        
        # Пул потоков для выполнения задач
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads)
        
        # Множество для хранения запущенных задач
        self.running_tasks = set()
        
        # Блокировка для потокобезопасного доступа к состоянию
        self.state_lock = asyncio.Lock()

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Обновление конфигурации планировщика.
        
        Args:
            config: Новая конфигурация.
        """
        self.config = config
        self.enabled = config.get('enabled', self.enabled)
        self.run_minutes = config.get('run_minutes', self.run_minutes)
        self.max_threads = config.get('max_threads', self.max_threads)
        self.run_on_start = config.get('run_on_start', self.run_on_start)
        
        # Обновление пула потоков, если изменилось максимальное количество потоков
        if hasattr(self, 'thread_pool') and self.thread_pool._max_workers != self.max_threads:
            old_pool = self.thread_pool
            self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads)
            old_pool.shutdown(wait=False)

    async def start(self) -> None:
        """Запуск планировщика."""
        if self.running:
            self.logger.warning("Планировщик уже запущен")
            return
        
        self.logger.info("Запуск планировщика...")
        
        # Создание процессора действий
        if self.executor is None:
            self.executor = ActionExecutor(
                self.device_manager,
                self.config_loader,
                self.logger,
                self.ui
            )
        
        # Установка флага работы
        async with self.state_lock:
            self.running = True
            self.paused = False
        
        # Запуск задачи планировщика
        if self.enabled:
            self.scheduler_task = asyncio.create_task(self._scheduler_task())
            self.logger.info("Планировщик успешно запущен")
        else:
            self.logger.info("Автоматический запуск по расписанию отключен")

    async def stop(self) -> None:
        """Остановка планировщика."""
        if not self.running:
            self.logger.warning("Планировщик не запущен")
            return
        
        self.logger.info("Остановка планировщика...")
        
        # Сброс флага работы
        async with self.state_lock:
            self.running = False
            self.paused = False
        
        # Остановка задачи планировщика
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None
        
        # Ожидание завершения выполняющихся задач
        remaining_tasks = list(self.running_tasks)
        if remaining_tasks:
            self.logger.info(f"Ожидание завершения {len(remaining_tasks)} выполняющихся задач...")
            try:
                await asyncio.gather(*remaining_tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"Ошибка при ожидании завершения задач: {e}")
        
        # Очистка множества задач
        self.running_tasks.clear()
        
        self.logger.info("Планировщик успешно остановлен")

    async def pause(self) -> None:
        """Приостановка планировщика."""
        if not self.running:
            self.logger.warning("Планировщик не запущен")
            return
        
        if self.paused:
            self.logger.warning("Планировщик уже приостановлен")
            return
        
        self.logger.info("Приостановка планировщика...")
        
        # Установка флага паузы
        async with self.state_lock:
            self.paused = True
        
        self.logger.info("Планировщик приостановлен")

    async def resume(self) -> None:
        """Возобновление работы планировщика."""
        if not self.running:
            self.logger.warning("Планировщик не запущен")
            return
        
        if not self.paused:
            self.logger.warning("Планировщик не находится в режиме паузы")
            return
        
        self.logger.info("Возобновление работы планировщика...")
        
        # Сброс флага паузы
        async with self.state_lock:
            self.paused = False
        
        self.logger.info("Работа планировщика возобновлена")

    async def _scheduler_task(self) -> None:
        """Фоновая задача для работы планировщика."""
        self.logger.info("Запуск фоновой задачи планировщика")
        
        try:
            while self.running:
                # Если планировщик находится в режиме паузы, пропускаем итерацию
                if self.paused:
                    await asyncio.sleep(1)
                    continue
                
                # Проверка, нужно ли запустить автоматизацию сейчас
                current_time = datetime.now()
                current_minute = current_time.minute
                
                if current_minute in self.run_minutes:
                    # Запуск автоматизации, если прошла предыдущая минута
                    previous_minute = (current_minute - 1) % 60
                    if previous_minute not in self.run_minutes:
                        self.ui.print_info(f"Запуск автоматизации по расписанию ({current_time.strftime('%H:%M')})")
                        await self.run_automation()
                
                # Ожидание 10 секунд перед следующей проверкой
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            self.logger.info("Задача планировщика отменена")
        except Exception as e:
            self.logger.exception(f"Ошибка в задаче планировщика: {e}")

    async def run_automation(self) -> bool:
        """
        Запуск автоматизации для всех устройств.
        
        Returns:
            bool: Успешен ли запуск.
        """
        try:
            # Проверка, запущен ли планировщик и не находится ли он в режиме паузы
            if not self.running:
                self.logger.warning("Планировщик не запущен")
                return False
            
            if self.paused:
                self.logger.warning("Планировщик находится в режиме паузы")
                return False
            
            self.logger.info("Запуск автоматизации...")
            
            # Загрузка всех конфигураций
            configs = self.config_loader.load_all_configs()
            
            if not configs:
                self.logger.warning("Нет доступных конфигураций для выполнения")
                return False
            
            # Получение списка партий устройств
            batches = await self.device_manager.get_device_batches()
            
            if not batches:
                self.logger.warning("Нет доступных устройств для автоматизации")
                return False
            
            # Запуск автоматизации для каждой партии устройств
            for i, batch in enumerate(batches):
                # Создание и запуск задачи для партии
                task = asyncio.create_task(self._run_batch(i, batch, configs))
                
                # Добавление задачи в множество
                self.running_tasks.add(task)
                
                # Добавление обработчика завершения
                task.add_done_callback(lambda t: self.running_tasks.discard(t))
                
                # Пауза перед запуском следующей партии
                await asyncio.sleep(self.config.get('thread_delay', 1))
            
            self.logger.info(f"Автоматизация запущена для {len(batches)} партий устройств")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при запуске автоматизации: {e}")
            return False

    async def _run_batch(
        self, 
        batch_index: int, 
        device_ids: List[str], 
        configs: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Запуск автоматизации для партии устройств.
        
        Args:
            batch_index: Индекс партии.
            device_ids: Список идентификаторов устройств в партии.
            configs: Словарь доступных конфигураций.
        """
        try:
            self.logger.info(f"Запуск партии {batch_index+1} ({len(device_ids)} устройств)")
            
            # Определение первой конфигурации для выполнения
            first_config = None
            for config_name, config_info in configs.items():
                # Выбираем первую валидную конфигурацию
                if self.config_loader.validate_config(config_name):
                    first_config = config_name
                    break
            
            if not first_config:
                self.logger.error("Не найдена валидная конфигурация для выполнения")
                return
            
            # Подключение устройств в партии
            connected_count, total_count = await self.device_manager.connect_batch(batch_index)
            
            self.logger.info(f"Подключено {connected_count} из {total_count} устройств в партии {batch_index+1}")
            
            # Запуск автоматизации для каждого подключенного устройства
            tasks = []
            for device_id in device_ids:
                # Проверка, подключено ли устройство
                if not await self.device_manager.device_connected(device_id):
                    continue
                
                # Создание и запуск задачи для устройства
                task = asyncio.create_task(
                    self._run_device_automation(device_id, first_config)
                )
                
                # Добавление задачи в список
                tasks.append(task)
            
            # Ожидание завершения всех задач
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.info(f"Партия {batch_index+1} завершена")
            
        except Exception as e:
            self.logger.exception(f"Ошибка при выполнении партии {batch_index+1}: {e}")

    async def _run_device_automation(
        self, 
        device_id: str, 
        config_name: str
    ) -> bool:
        """
        Запуск автоматизации для конкретного устройства.
        
        Args:
            device_id: Идентификатор устройства.
            config_name: Имя конфигурации для выполнения.
            
        Returns:
            bool: Успешно ли выполнение автоматизации.
        """
        try:
            self.logger.info(f"Запуск автоматизации для устройства {device_id} с конфигурацией {config_name}")
            
            # Получение логгера для устройства
            device_logger = await self.device_manager.get_device_logger(device_id)
            
            # Выполнение конфигурации
            success = await self.executor.execute_config(device_id, config_name, device_logger)
            
            if success:
                self.logger.info(f"Автоматизация успешно выполнена для устройства {device_id}")
                
                # Проверка наличия следующей конфигурации
                next_config = self.config_loader.get_config_next_config(config_name)
                if next_config:
                    self.logger.info(f"Запуск следующей конфигурации {next_config} для устройства {device_id}")
                    return await self._run_device_automation(device_id, next_config)
                
                return True
            else:
                self.logger.warning(f"Ошибка при выполнении автоматизации для устройства {device_id}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Ошибка при выполнении автоматизации для устройства {device_id}: {e}")
            return False

    async def run_specific_config(self, config_name: str) -> bool:
        """
        Запуск конкретной конфигурации для всех устройств.
        
        Args:
            config_name: Имя конфигурации для выполнения.
            
        Returns:
            bool: Успешен ли запуск.
        """
        try:
            self.logger.info(f"Запуск конфигурации {config_name} для всех устройств")
            
            # Проверка существования и валидности конфигурации
            if not self.config_loader.validate_config(config_name):
                self.logger.error(f"Конфигурация {config_name} не найдена или не валидна")
                return False
            
            # Получение списка партий устройств
            batches = await self.device_manager.get_device_batches()
            
            if not batches:
                self.logger.warning("Нет доступных устройств для автоматизации")
                return False
            
            # Запуск автоматизации для каждой партии устройств
            for i, batch in enumerate(batches):
                # Создание и запуск задачи для партии
                task = asyncio.create_task(
                    self._run_specific_config_batch(i, batch, config_name)
                )
                
                # Добавление задачи в множество
                self.running_tasks.add(task)
                
                # Добавление обработчика завершения
                task.add_done_callback(lambda t: self.running_tasks.discard(t))
                
                # Пауза перед запуском следующей партии
                await asyncio.sleep(self.config.get('thread_delay', 1))
            
            self.logger.info(f"Конфигурация {config_name} запущена для {len(batches)} партий устройств")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при запуске конфигурации {config_name}: {e}")
            return False

    async def _run_specific_config_batch(
        self, 
        batch_index: int, 
        device_ids: List[str], 
        config_name: str
    ) -> None:
        """
        Запуск конкретной конфигурации для партии устройств.
        
        Args:
            batch_index: Индекс партии.
            device_ids: Список идентификаторов устройств в партии.
            config_name: Имя конфигурации для выполнения.
        """
        try:
            self.logger.info(f"Запуск конфигурации {config_name} для партии {batch_index+1} ({len(device_ids)} устройств)")
            
            # Подключение устройств в партии
            connected_count, total_count = await self.device_manager.connect_batch(batch_index)
            
            self.logger.info(f"Подключено {connected_count} из {total_count} устройств в партии {batch_index+1}")
            
            # Запуск автоматизации для каждого подключенного устройства
            tasks = []
            for device_id in device_ids:
                # Проверка, подключено ли устройство
                if not await self.device_manager.device_connected(device_id):
                    continue
                
                # Создание и запуск задачи для устройства
                task = asyncio.create_task(
                    self._run_device_automation(device_id, config_name)
                )
                
                # Добавление задачи в список
                tasks.append(task)
            
            # Ожидание завершения всех задач
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.info(f"Партия {batch_index+1} с конфигурацией {config_name} завершена")
            
        except Exception as e:
            self.logger.exception(f"Ошибка при выполнении партии {batch_index+1} с конфигурацией {config_name}: {e}")

    async def stop_automation(self) -> bool:
        """
        Остановка выполняющейся автоматизации.
        
        Returns:
            bool: Успешна ли остановка.
        """
        try:
            self.logger.info("Остановка выполняющейся автоматизации")
            
            # Остановка выполнения в процессоре действий
            if self.executor:
                await self.executor.stop_execution()
            
            # Отмена всех выполняющихся задач
            tasks = list(self.running_tasks)
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Ожидание завершения всех задач
            if tasks:
                self.logger.info(f"Ожидание завершения {len(tasks)} задач")
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Очистка множества задач
            self.running_tasks.clear()
            
            self.logger.info("Автоматизация успешно остановлена")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при остановке автоматизации: {e}")
            return False

    async def pause_automation(self) -> bool:
        """
        Приостановка выполняющейся автоматизации.
        
        Returns:
            bool: Успешна ли приостановка.
        """
        try:
            self.logger.info("Приостановка выполняющейся автоматизации")
            
            # Приостановка выполнения в процессоре действий
            if self.executor:
                await self.executor.pause_execution()
            
            # Установка флага паузы в планировщике
            await self.pause()
            
            self.logger.info("Автоматизация успешно приостановлена")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при приостановке автоматизации: {e}")
            return False

    async def resume_automation(self) -> bool:
        """
        Возобновление выполнения приостановленной автоматизации.
        
        Returns:
            bool: Успешно ли возобновление.
        """
        try:
            self.logger.info("Возобновление выполнения автоматизации")
            
            # Возобновление выполнения в процессоре действий
            if self.executor:
                await self.executor.resume_execution()
            
            # Сброс флага паузы в планировщике
            await self.resume()
            
            self.logger.info("Выполнение автоматизации успешно возобновлено")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при возобновлении автоматизации: {e}")
            return False

    async def is_automation_running(self) -> bool:
        """
        Проверка, выполняется ли автоматизация в данный момент.
        
        Returns:
            bool: Выполняется ли автоматизация.
        """
        # Проверка наличия запущенных задач
        return len(self.running_tasks) > 0

    async def is_automation_paused(self) -> bool:
        """
        Проверка, приостановлена ли автоматизация.
        
        Returns:
            bool: Приостановлена ли автоматизация.
        """
        # Проверка флага паузы в планировщике и процессоре действий
        return self.paused and (self.executor and await self.executor.is_paused())

    async def get_running_configs(self) -> List[str]:
        """
        Получение списка выполняющихся конфигураций.
        
        Returns:
            List[str]: Список имен выполняющихся конфигураций.
        """
        if self.executor:
            return await self.executor.get_running_configs()
        return []

    async def get_running_devices(self) -> List[str]:
        """
        Получение списка устройств, на которых выполняется автоматизация.
        
        Returns:
            List[str]: Список идентификаторов устройств.
        """
        if self.executor:
            return await self.executor.get_running_devices()
        return []