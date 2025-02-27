#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления устройствами в ADB Блюстакс Автоматизация.
Обеспечивает работу с устройствами, их подключение, отключение и получение информации.
"""

import os
import re
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import concurrent.futures
from modules.logger import get_device_logger


class DeviceManager:
    """
    Класс для управления устройствами в ADB Блюстакс Автоматизация.
    Обеспечивает подключение, отключение и отслеживание состояния устройств.
    """

    def __init__(self, config: Dict[str, Any], adb_manager, logger: logging.Logger, ui):
        """
        Инициализация менеджера устройств.
        
        Args:
            config: Конфигурация управления устройствами.
            adb_manager: Экземпляр менеджера ADB.
            logger: Логгер для записи событий.
            ui: Интерфейс пользователя для вывода информации.
        """
        self.config = config
        self.adb_manager = adb_manager
        self.logger = logger
        self.ui = ui
        
        # Файл со списком устройств
        self.devices_file = config.get('devices_file', 'configs/devices.txt')
        
        # Размер пакета для параллельной обработки устройств
        self.batch_size = config.get('batch_size', 10)
        
        # Задержка между запуском потоков в секундах
        self.thread_delay = config.get('thread_delay', 1)
        
        # Таймаут подключения к устройству в секундах
        self.connect_timeout = config.get('connect_timeout', 15)
        
        # Автоматическое переподключение к устройствам
        self.auto_reconnect = config.get('auto_reconnect', True)
        
        # Интервал проверки состояния устройств в секундах
        self.status_check_interval = config.get('status_check_interval', 60)
        
        # Словарь устройств в формате {device_id: {...}}
        self.devices = {}
        
        # Словарь логгеров для устройств
        self.device_loggers = {}
        
        # Флаги и блокировки
        self.running = False
        self.device_lock = asyncio.Lock()
        
        # Состояние задач
        self.device_tasks = set()
        self.background_tasks = set()

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Обновление конфигурации менеджера устройств.
        
        Args:
            config: Новая конфигурация.
        """
        self.config = config
        self.devices_file = config.get('devices_file', self.devices_file)
        self.batch_size = config.get('batch_size', self.batch_size)
        self.thread_delay = config.get('thread_delay', self.thread_delay)
        self.connect_timeout = config.get('connect_timeout', self.connect_timeout)
        self.auto_reconnect = config.get('auto_reconnect', self.auto_reconnect)
        self.status_check_interval = config.get('status_check_interval', self.status_check_interval)

    async def load_devices(self) -> bool:
        """
        Загрузка списка устройств из файла.
        
        Returns:
            bool: Успешна ли загрузка.
        """
        try:
            self.logger.info(f"Загрузка списка устройств из файла {self.devices_file}")
            
            # Проверка существования файла
            if not os.path.exists(self.devices_file):
                self.logger.error(f"Файл со списком устройств не найден: {self.devices_file}")
                return False
            
            # Чтение файла
            with open(self.devices_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Разбор строк файла
            async with self.device_lock:
                self.devices = {}
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Разбор строки в формате IP:порт:название или IP:порт
                    parts = line.split(':')
                    if len(parts) >= 2:
                        # Получение IP и порта
                        ip = parts[0]
                        port = parts[1]
                        device_id = f"{ip}:{port}"
                        
                        # Получение названия, если оно указано
                        name = parts[2] if len(parts) > 2 else f"Устройство {device_id}"
                        
                        # Добавление устройства в словарь
                        self.devices[device_id] = {
                            'id': device_id,
                            'name': name,
                            'ip': ip,
                            'port': port,
                            'connected': False,
                            'status': 'Не подключено',
                            'last_connection_attempt': 0,
                            'connection_attempts': 0,
                            'current_action': None,
                            'info': {}
                        }
                        
                        # Создание логгера для устройства
                        if device_id not in self.device_loggers:
                            self.device_loggers[device_id] = get_device_logger(
                                device_id, 
                                self.logger,
                                directory=os.path.join('logs', 'devices')
                            )
            
            self.logger.info(f"Загружено {len(self.devices)} устройств из файла")
            
            # Запуск фоновой задачи проверки состояния устройств
            if self.auto_reconnect and self.status_check_interval > 0:
                self._start_status_check_task()
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при загрузке списка устройств: {e}")
            return False

    def _start_status_check_task(self) -> None:
        """Запуск фоновой задачи для проверки состояния устройств."""
        # Остановка существующей задачи, если она есть
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Создание новой задачи
        task = asyncio.create_task(self._check_devices_status_task())
        
        # Добавление обработчика завершения
        task.add_done_callback(self.background_tasks.discard)
        
        # Добавление задачи в множество
        self.background_tasks.add(task)

    async def _check_devices_status_task(self) -> None:
        """Фоновая задача для периодической проверки состояния устройств."""
        self.logger.info(f"Запущена фоновая задача проверки состояния устройств (интервал: {self.status_check_interval}с)")
        
        try:
            while True:
                # Проверка состояния устройств
                await self.update_device_statuses()
                
                # Попытка переподключения отключенных устройств
                if self.auto_reconnect:
                    await self._reconnect_disconnected_devices()
                
                # Ожидание следующей проверки
                await asyncio.sleep(self.status_check_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Задача проверки состояния устройств остановлена")
        except Exception as e:
            self.logger.exception(f"Ошибка в задаче проверки состояния устройств: {e}")

    async def _reconnect_disconnected_devices(self) -> None:
        """Попытка переподключения к отключенным устройствам."""
        disconnected_devices = []
        
        # Поиск отключенных устройств
        async with self.device_lock:
            for device_id, device_info in self.devices.items():
                if not device_info['connected']:
                    # Проверка времени последней попытки подключения
                    current_time = time.time()
                    last_attempt = device_info['last_connection_attempt']
                    
                    # Подключаемся, только если прошло достаточно времени с последней попытки
                    if current_time - last_attempt >= self.connect_timeout:
                        disconnected_devices.append(device_id)
        
        # Попытка переподключения к каждому устройству
        for device_id in disconnected_devices:
            self.logger.debug(f"Попытка переподключения к устройству {device_id}")
            await self.connect_device(device_id)

    async def update_device_statuses(self) -> None:
        """Обновление статусов всех устройств."""
        try:
            # Получение списка подключенных устройств через ADB
            adb_devices = await self.adb_manager.get_devices()
            
            # Словарь для соответствия ID устройств и их состояния
            adb_device_states = {device['id']: device['state'] for device in adb_devices}
            
            # Обновление статусов устройств
            async with self.device_lock:
                for device_id, device_info in self.devices.items():
                    if device_id in adb_device_states:
                        # Устройство найдено в списке ADB
                        state = adb_device_states[device_id]
                        
                        if state == 'device':
                            device_info['connected'] = True
                            device_info['status'] = 'Подключено'
                            device_info['connection_attempts'] = 0
                        else:
                            device_info['connected'] = False
                            device_info['status'] = f"Не готово ({state})"
                    else:
                        # Устройство не найдено в списке ADB
                        device_info['connected'] = False
                        device_info['status'] = 'Отключено'
                
            self.logger.debug("Статусы устройств успешно обновлены")
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении статусов устройств: {e}")

    async def connect_device(self, device_id: str) -> bool:
        """
        Подключение к устройству.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            bool: Успешно ли подключение.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка подключения к неизвестному устройству: {device_id}")
                return False
            
            # Обновление информации о попытке подключения
            async with self.device_lock:
                self.devices[device_id]['last_connection_attempt'] = time.time()
                self.devices[device_id]['connection_attempts'] += 1
            
            # Подключение к устройству через ADB
            success = await self.adb_manager.connect_device(device_id)
            
            # Обновление статуса устройства
            if success:
                logger = self.device_loggers.get(device_id, self.logger)
                logger.info(f"Устройство {device_id} успешно подключено")
                
                # Обновление информации об устройстве
                device_info = await self.adb_manager.get_device_info(device_id)
                
                async with self.device_lock:
                    self.devices[device_id]['connected'] = True
                    self.devices[device_id]['status'] = 'Подключено'
                    self.devices[device_id]['info'] = device_info
                
                # Вывод информации в UI
                device_name = self.devices[device_id]['name']
                self.ui.print_device_message(device_id, f"Устройство {device_name} подключено", "INFO")
                
                return True
            else:
                logger = self.device_loggers.get(device_id, self.logger)
                logger.warning(f"Не удалось подключиться к устройству {device_id}")
                
                async with self.device_lock:
                    self.devices[device_id]['connected'] = False
                    self.devices[device_id]['status'] = 'Ошибка подключения'
                
                # Вывод информации в UI (только если это не автоматическая попытка переподключения)
                if self.devices[device_id]['connection_attempts'] <= 1:
                    device_name = self.devices[device_id]['name']
                    self.ui.print_device_message(device_id, f"Ошибка подключения к устройству {device_name}", "ERROR")
                
                return False
                
        except Exception as e:
            self.logger.exception(f"Ошибка при подключении к устройству {device_id}: {e}")
            
            async with self.device_lock:
                self.devices[device_id]['connected'] = False
                self.devices[device_id]['status'] = 'Ошибка подключения'
            
            return False

    async def disconnect_device(self, device_id: str) -> bool:
        """
        Отключение от устройства.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            bool: Успешно ли отключение.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка отключения от неизвестного устройства: {device_id}")
                return False
            
            # Отключение от устройства через ADB
            success = await self.adb_manager.disconnect_device(device_id)
            
            # Обновление статуса устройства
            async with self.device_lock:
                self.devices[device_id]['connected'] = False
                self.devices[device_id]['status'] = 'Отключено'
                self.devices[device_id]['current_action'] = None
            
            logger = self.device_loggers.get(device_id, self.logger)
            device_name = self.devices[device_id]['name']
            
            if success:
                logger.info(f"Устройство {device_id} успешно отключено")
                self.ui.print_device_message(device_id, f"Устройство {device_name} отключено", "INFO")
                return True
            else:
                logger.warning(f"Проблема при отключении от устройства {device_id}")
                self.ui.print_device_message(device_id, f"Проблема при отключении от устройства {device_name}", "WARNING")
                return False
                
        except Exception as e:
            self.logger.exception(f"Ошибка при отключении от устройства {device_id}: {e}")
            
            async with self.device_lock:
                self.devices[device_id]['connected'] = False
                self.devices[device_id]['status'] = 'Ошибка отключения'
            
            return False

    async def disconnect_all(self) -> int:
        """
        Отключение от всех устройств.
        
        Returns:
            int: Количество успешно отключенных устройств.
        """
        success_count = 0
        
        # Получение списка устройств
        device_ids = list(self.devices.keys())
        
        # Отключение от каждого устройства
        for device_id in device_ids:
            if await self.disconnect_device(device_id):
                success_count += 1
        
        self.logger.info(f"Отключено {success_count} из {len(device_ids)} устройств")
        return success_count

    async def connect_all(self) -> int:
        """
        Подключение ко всем устройствам из списка.
        
        Returns:
            int: Количество успешно подключенных устройств.
        """
        success_count = 0
        
        # Получение списка устройств
        device_ids = list(self.devices.keys())
        
        # Подключение к каждому устройству
        for device_id in device_ids:
            if await self.connect_device(device_id):
                success_count += 1
        
        self.logger.info(f"Подключено {success_count} из {len(device_ids)} устройств")
        return success_count

    async def connect_batch(self, batch_index: int, batch_size: Optional[int] = None) -> Tuple[int, int]:
        """
        Подключение к партии устройств для параллельной обработки.
        
        Args:
            batch_index: Индекс партии.
            batch_size: Размер партии (по умолчанию из конфигурации).
            
        Returns:
            Tuple[int, int]: Количество успешно подключенных устройств и общее количество устройств в партии.
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        # Получение списка устройств
        device_ids = list(self.devices.keys())
        total_devices = len(device_ids)
        
        # Вычисление индексов начала и конца партии
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, total_devices)
        
        # Проверка корректности индексов
        if start_index >= total_devices:
            self.logger.warning(f"Индекс партии {batch_index} выходит за пределы списка устройств")
            return 0, 0
        
        # Получение списка устройств для текущей партии
        batch_devices = device_ids[start_index:end_index]
        batch_size_actual = len(batch_devices)
        
        self.logger.info(f"Подключение к партии устройств {batch_index+1} ({start_index+1}-{end_index} из {total_devices})")
        
        # Подключение к каждому устройству в партии
        success_count = 0
        for device_id in batch_devices:
            if await self.connect_device(device_id):
                success_count += 1
        
        self.logger.info(f"Подключено {success_count} из {batch_size_actual} устройств в партии {batch_index+1}")
        return success_count, batch_size_actual

    async def device_exists(self, device_id: str) -> bool:
        """
        Проверка существования устройства в списке.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            bool: Существует ли устройство.
        """
        return device_id in self.devices

    async def device_connected(self, device_id: str) -> bool:
        """
        Проверка, подключено ли устройство.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            bool: Подключено ли устройство.
        """
        # Проверка, существует ли устройство в списке
        if device_id not in self.devices:
            return False
        
        # Проверка статуса подключения
        return self.devices[device_id]['connected']

    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """
        Получение информации об устройстве.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            Dict[str, Any]: Информация об устройстве.
        """
        # Проверка, существует ли устройство в списке
        if device_id not in self.devices:
            return {}
        
        # Если устройство не подключено, возвращаем только базовую информацию
        if not self.devices[device_id]['connected']:
            return {
                'id': device_id,
                'name': self.devices[device_id]['name'],
                'connected': False
            }
        
        # Получение информации через ADB
        info = await self.adb_manager.get_device_info(device_id)
        
        # Дополнение информации данными из нашего списка
        info['name'] = self.devices[device_id]['name']
        
        return info

    async def update_device_action(self, device_id: str, action: Optional[str]) -> bool:
        """
        Обновление текущего действия устройства.
        
        Args:
            device_id: Идентификатор устройства.
            action: Описание текущего действия (None для сброса).
            
        Returns:
            bool: Успешно ли обновление.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                return False
            
            # Обновление информации о текущем действии
            async with self.device_lock:
                self.devices[device_id]['current_action'] = action
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении действия устройства {device_id}: {e}")
            return False

    async def take_screenshot(self, device_id: str) -> Optional[str]:
        """
        Создание скриншота устройства.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            Optional[str]: Путь к сохраненному скриншоту или None в случае ошибки.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка создания скриншота неизвестного устройства: {device_id}")
                return None
            
            # Проверка, подключено ли устройство
            if not self.devices[device_id]['connected']:
                self.logger.warning(f"Попытка создания скриншота неподключенного устройства: {device_id}")
                self.ui.print_device_message(device_id, "Невозможно создать скриншот: устройство не подключено", "WARNING")
                return None
            
            # Обновление действия устройства
            await self.update_device_action(device_id, "Создание скриншота")
            
            # Создание скриншота через ADB
            screenshot_path = await self.adb_manager.take_screenshot(device_id)
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            if screenshot_path:
                device_name = self.devices[device_id]['name']
                self.ui.print_device_message(device_id, f"Скриншот сохранен: {screenshot_path}", "INFO")
                return screenshot_path
            else:
                self.ui.print_device_message(device_id, "Ошибка при создании скриншота", "ERROR")
                return None
                
        except Exception as e:
            self.logger.exception(f"Ошибка при создании скриншота устройства {device_id}: {e}")
            self.ui.print_device_message(device_id, f"Ошибка при создании скриншота: {e}", "ERROR")
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return None

    async def execute_adb_command(
        self, 
        device_id: str, 
        command: List[str], 
        action_description: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Выполнение ADB-команды для устройства с обновлением статуса.
        
        Args:
            device_id: Идентификатор устройства.
            command: Список аргументов команды.
            action_description: Описание действия для отображения в статусе.
            
        Returns:
            Tuple[bool, str, str]: Успех, стандартный вывод, стандартный вывод ошибок.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка выполнения команды для неизвестного устройства: {device_id}")
                return False, "", "Устройство не найдено в списке"
            
            # Проверка, подключено ли устройство
            if not self.devices[device_id]['connected']:
                self.logger.warning(f"Попытка выполнения команды для неподключенного устройства: {device_id}")
                return False, "", "Устройство не подключено"
            
            # Обновление действия устройства
            if action_description:
                await self.update_device_action(device_id, action_description)
            
            # Выполнение команды через ADB
            success, stdout, stderr = await self.adb_manager.execute_command(device_id, command)
            
            # Сброс действия устройства
            if action_description:
                await self.update_device_action(device_id, None)
            
            return success, stdout, stderr
            
        except Exception as e:
            self.logger.exception(f"Ошибка при выполнении команды для устройства {device_id}: {e}")
            
            # Сброс действия устройства
            if action_description:
                await self.update_device_action(device_id, None)
            
            return False, "", str(e)

    async def execute_shell_command(
        self, 
        device_id: str, 
        command: str, 
        action_description: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Выполнение shell-команды для устройства с обновлением статуса.
        
        Args:
            device_id: Идентификатор устройства.
            command: Shell-команда.
            action_description: Описание действия для отображения в статусе.
            
        Returns:
            Tuple[bool, str, str]: Успех, стандартный вывод, стандартный вывод ошибок.
        """
        return await self.execute_adb_command(device_id, ['shell', command], action_description)

    async def restart_app(
        self, 
        device_id: str, 
        package_name: str, 
        action_description: Optional[str] = None
    ) -> bool:
        """
        Перезапуск приложения на устройстве с обновлением статуса.
        
        Args:
            device_id: Идентификатор устройства.
            package_name: Имя пакета приложения.
            action_description: Описание действия для отображения в статусе.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка перезапуска приложения для неизвестного устройства: {device_id}")
                return False
            
            # Проверка, подключено ли устройство
            if not self.devices[device_id]['connected']:
                self.logger.warning(f"Попытка перезапуска приложения для неподключенного устройства: {device_id}")
                return False
            
            # Обновление действия устройства
            description = action_description or f"Перезапуск {package_name}"
            await self.update_device_action(device_id, description)
            
            # Перезапуск приложения через ADB
            success = await self.adb_manager.restart_app(device_id, package_name)
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return success
            
        except Exception as e:
            self.logger.exception(f"Ошибка при перезапуске приложения для устройства {device_id}: {e}")
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return False

    async def input_tap(
        self, 
        device_id: str, 
        x: int, 
        y: int, 
        action_description: Optional[str] = None
    ) -> bool:
        """
        Симуляция нажатия на экран устройства с обновлением статуса.
        
        Args:
            device_id: Идентификатор устройства.
            x: Координата X.
            y: Координата Y.
            action_description: Описание действия для отображения в статусе.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка нажатия для неизвестного устройства: {device_id}")
                return False
            
            # Проверка, подключено ли устройство
            if not self.devices[device_id]['connected']:
                self.logger.warning(f"Попытка нажатия для неподключенного устройства: {device_id}")
                return False
            
            # Обновление действия устройства
            description = action_description or f"Нажатие ({x}, {y})"
            await self.update_device_action(device_id, description)
            
            # Выполнение нажатия через ADB
            success = await self.adb_manager.input_tap(device_id, x, y)
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return success
            
        except Exception as e:
            self.logger.exception(f"Ошибка при выполнении нажатия для устройства {device_id}: {e}")
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return False

    async def input_text(
        self, 
        device_id: str, 
        text: str, 
        action_description: Optional[str] = None
    ) -> bool:
        """
        Ввод текста на устройстве с обновлением статуса.
        
        Args:
            device_id: Идентификатор устройства.
            text: Текст для ввода.
            action_description: Описание действия для отображения в статусе.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            # Проверка, существует ли устройство в списке
            if device_id not in self.devices:
                self.logger.warning(f"Попытка ввода текста для неизвестного устройства: {device_id}")
                return False
            
            # Проверка, подключено ли устройство
            if not self.devices[device_id]['connected']:
                self.logger.warning(f"Попытка ввода текста для неподключенного устройства: {device_id}")
                return False
            
            # Обновление действия устройства
            description = action_description or f"Ввод текста"
            await self.update_device_action(device_id, description)
            
            # Выполнение ввода текста через ADB
            success = await self.adb_manager.input_text(device_id, text)
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return success
            
        except Exception as e:
            self.logger.exception(f"Ошибка при вводе текста для устройства {device_id}: {e}")
            
            # Сброс действия устройства
            await self.update_device_action(device_id, None)
            
            return False

    async def get_device_logger(self, device_id: str) -> logging.Logger:
        """
        Получение логгера для конкретного устройства.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            logging.Logger: Логгер устройства.
        """
        # Проверка, существует ли устройство в списке
        if device_id not in self.devices:
            self.logger.warning(f"Попытка получения логгера для неизвестного устройства: {device_id}")
            return self.logger
        
        # Создание логгера, если он не существует
        if device_id not in self.device_loggers:
            self.device_loggers[device_id] = get_device_logger(
                device_id, 
                self.logger,
                directory=os.path.join('logs', 'devices')
            )
        
        return self.device_loggers[device_id]

    async def get_connected_devices(self) -> List[str]:
        """
        Получение списка подключенных устройств.
        
        Returns:
            List[str]: Список идентификаторов подключенных устройств.
        """
        connected_devices = []
        
        async with self.device_lock:
            for device_id, device_info in self.devices.items():
                if device_info['connected']:
                    connected_devices.append(device_id)
        
        return connected_devices

    async def get_devices_count(self) -> Tuple[int, int]:
        """
        Получение количества устройств и количества подключенных устройств.
        
        Returns:
            Tuple[int, int]: Общее количество устройств и количество подключенных устройств.
        """
        total_count = len(self.devices)
        connected_count = 0
        
        async with self.device_lock:
            for device_info in self.devices.values():
                if device_info['connected']:
                    connected_count += 1
        
        return total_count, connected_count

    async def get_device_batches(self) -> List[List[str]]:
        """
        Получение списка партий устройств для параллельной обработки.
        
        Returns:
            List[List[str]]: Список партий с идентификаторами устройств.
        """
        # Получение списка всех устройств
        device_ids = list(self.devices.keys())
        total_devices = len(device_ids)
        
        # Разделение устройств на партии
        batches = []
        for i in range(0, total_devices, self.batch_size):
            batches.append(device_ids[i:i + self.batch_size])
        
        return batches