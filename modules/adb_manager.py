#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для управления ADB-подключениями в ADB Блюстакс Автоматизация.
Предоставляет интерфейс для выполнения ADB-команд и управления ADB-сервером.
"""

import os
import sys
import re
import time
import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union
import adbutils


class ADBManager:
    """
    Класс для управления ADB-подключениями и выполнения ADB-команд.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger, ui):
        """
        Инициализация менеджера ADB.
        
        Args:
            config: Конфигурация ADB.
            logger: Логгер для записи событий.
            ui: Интерфейс пользователя для вывода информации.
        """
        self.config = config
        self.logger = logger
        self.ui = ui
        
        # Путь к исполняемому файлу ADB
        self.adb_path = config.get('path', '') or 'adb'
        
        # Порт для ADB сервера
        self.port = config.get('port', 5037)
        
        # Время ожидания для ADB-команд в секундах
        self.timeout = config.get('timeout', 10)
        
        # Максимальное количество повторных попыток для ADB-команд
        self.max_retries = config.get('max_retries', 3)
        
        # Интервал между повторными попытками в секундах
        self.retry_interval = config.get('retry_interval', 2)
        
        # Клиент ADB
        self.adb = None
        
        # Режим отладки
        self.debug = config.get('debug', False)

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Обновление конфигурации ADB.
        
        Args:
            config: Новая конфигурация.
        """
        self.config = config
        self.adb_path = config.get('path', self.adb_path) or 'adb'
        self.port = config.get('port', self.port)
        self.timeout = config.get('timeout', self.timeout)
        self.max_retries = config.get('max_retries', self.max_retries)
        self.retry_interval = config.get('retry_interval', self.retry_interval)
        self.debug = config.get('debug', self.debug)

    async def initialize(self) -> bool:
        """
        Инициализация ADB сервера и проверка доступности.
        
        Returns:
            bool: Успешна ли инициализация.
        """
        try:
            self.logger.info("Инициализация ADB менеджера...")
            
            # Проверка наличия ADB
            await self._check_adb_availability()
            
            # Запуск ADB сервера, если он не запущен
            if not await self.is_server_running():
                self.logger.info("ADB сервер не запущен. Запуск...")
                await self.start_server()
            
            # Создание ADB клиента
            self.adb = adbutils.AdbClient(host='127.0.0.1', port=self.port)
            
            # Проверка версии ADB
            version = await self.get_version()
            self.logger.info(f"ADB версия: {version}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации ADB: {e}")
            return False

    async def _check_adb_availability(self) -> bool:
        """
        Проверка доступности ADB в системе.
        
        Returns:
            bool: Доступен ли ADB.
            
        Raises:
            Exception: Если ADB не найден в системе.
        """
        try:
            # Выполнение команды для проверки ADB
            process = await asyncio.create_subprocess_exec(
                self.adb_path, 'version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ожидание завершения процесса с таймаутом
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise Exception("Таймаут при проверке ADB")
            
            # Проверка кода возврата
            if process.returncode != 0:
                stderr_text = stderr.decode('utf-8', errors='replace')
                raise Exception(f"Ошибка ADB: {stderr_text}")
            
            return True
            
        except FileNotFoundError:
            raise Exception(f"ADB не найден. Проверьте установку ADB или путь: {self.adb_path}")
        except Exception as e:
            raise Exception(f"Ошибка при проверке ADB: {e}")

    async def is_server_running(self) -> bool:
        """
        Проверка, запущен ли ADB сервер.
        
        Returns:
            bool: Запущен ли сервер.
        """
        try:
            # Попытка подключения к серверу
            process = await asyncio.create_subprocess_exec(
                self.adb_path, 'devices',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ожидание завершения процесса с таймаутом
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2)
            except asyncio.TimeoutError:
                process.kill()
                return False
            
            # Если код возврата 0, сервер запущен
            return process.returncode == 0
            
        except Exception:
            return False

    async def start_server(self) -> bool:
        """
        Запуск ADB сервера.
        
        Returns:
            bool: Успешен ли запуск.
        """
        try:
            self.logger.info("Запуск ADB сервера...")
            
            # Запуск сервера
            process = await asyncio.create_subprocess_exec(
                self.adb_path, 'start-server',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ожидание завершения процесса с таймаутом
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                process.kill()
                self.logger.error("Таймаут при запуске ADB сервера")
                return False
            
            # Проверка кода возврата
            if process.returncode != 0:
                stderr_text = stderr.decode('utf-8', errors='replace')
                self.logger.error(f"Ошибка при запуске ADB сервера: {stderr_text}")
                return False
            
            # Пауза для стабилизации сервера
            await asyncio.sleep(1)
            
            # Проверка, запущен ли сервер
            if await self.is_server_running():
                self.logger.info("ADB сервер успешно запущен")
                return True
            else:
                self.logger.error("ADB сервер не запустился")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка при запуске ADB сервера: {e}")
            return False

    async def stop_server(self) -> bool:
        """
        Остановка ADB сервера.
        
        Returns:
            bool: Успешна ли остановка.
        """
        try:
            self.logger.info("Остановка ADB сервера...")
            
            # Остановка сервера
            process = await asyncio.create_subprocess_exec(
                self.adb_path, 'kill-server',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ожидание завершения процесса с таймаутом
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                process.kill()
                self.logger.error("Таймаут при остановке ADB сервера")
                return False
            
            # Проверка, остановлен ли сервер
            if not await self.is_server_running():
                self.logger.info("ADB сервер успешно остановлен")
                return True
            else:
                self.logger.error("ADB сервер не остановился")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка при остановке ADB сервера: {e}")
            return False

    async def get_version(self) -> str:
        """
        Получение версии ADB.
        
        Returns:
            str: Версия ADB.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                self.adb_path, 'version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode('utf-8', errors='replace')
            
            # Попытка получить версию из вывода
            match = re.search(r'Android Debug Bridge version ([\d\.]+)', stdout_text)
            if match:
                return match.group(1)
            else:
                return "Неизвестно"
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении версии ADB: {e}")
            return "Ошибка"

    async def get_devices(self) -> List[Dict[str, str]]:
        """
        Получение списка подключенных устройств.
        
        Returns:
            List[Dict[str, str]]: Список устройств в формате [{'id': 'device_id', 'state': 'device|offline|...'}].
        """
        devices = []
        try:
            # Использование adbutils для получения списка устройств
            adb_devices = self.adb.device_list()
            
            for device in adb_devices:
                devices.append({
                    'id': device.serial,
                    'state': device.status
                })
                
            return devices
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении списка устройств: {e}")
            return []

    async def connect_device(self, device_id: str) -> bool:
        """
        Подключение к устройству по IP и порту.
        
        Args:
            device_id: Идентификатор устройства в формате IP:порт.
            
        Returns:
            bool: Успешно ли подключение.
        """
        # Проверка, содержит ли идентификатор порт
        if ':' in device_id:
            try:
                # Разбор IP и порта
                ip_port = device_id
                
                # Выполнение команды подключения
                for attempt in range(self.max_retries):
                    try:
                        self.logger.debug(f"Попытка подключения к {ip_port} (попытка {attempt+1}/{self.max_retries})...")
                        
                        process = await asyncio.create_subprocess_exec(
                            self.adb_path, 'connect', ip_port,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        
                        stdout, stderr = await asyncio.wait_for(
                            process.communicate(), 
                            timeout=self.timeout
                        )
                        
                        stdout_text = stdout.decode('utf-8', errors='replace')
                        
                        # Проверка успешности подключения
                        if 'connected to' in stdout_text.lower() and 'cannot' not in stdout_text.lower():
                            self.logger.info(f"Устройство {ip_port} успешно подключено")
                            return True
                        
                        # Если устройство уже подключено
                        if 'already connected' in stdout_text.lower():
                            self.logger.info(f"Устройство {ip_port} уже подключено")
                            return True
                            
                        # Пауза перед следующей попыткой
                        await asyncio.sleep(self.retry_interval)
                        
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Таймаут при подключении к {ip_port}")
                        # Пауза перед следующей попыткой
                        await asyncio.sleep(self.retry_interval)
                
                self.logger.error(f"Не удалось подключиться к {ip_port} после {self.max_retries} попыток")
                return False
                
            except Exception as e:
                self.logger.error(f"Ошибка при подключении к {device_id}: {e}")
                return False
        else:
            # Если устройство подключено локально, считаем его подключенным
            self.logger.info(f"Устройство {device_id} подключено локально")
            return True

    async def disconnect_device(self, device_id: str) -> bool:
        """
        Отключение от устройства.
        
        Args:
            device_id: Идентификатор устройства в формате IP:порт.
            
        Returns:
            bool: Успешно ли отключение.
        """
        # Проверка, содержит ли идентификатор порт
        if ':' in device_id:
            try:
                # Разбор IP и порта
                ip_port = device_id
                
                # Выполнение команды отключения
                process = await asyncio.create_subprocess_exec(
                    self.adb_path, 'disconnect', ip_port,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
                
                stdout_text = stdout.decode('utf-8', errors='replace')
                
                # Проверка успешности отключения
                if 'disconnected' in stdout_text.lower() or process.returncode == 0:
                    self.logger.info(f"Устройство {ip_port} успешно отключено")
                    return True
                else:
                    self.logger.warning(f"Проблема при отключении от {ip_port}: {stdout_text}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Ошибка при отключении от {device_id}: {e}")
                return False
        else:
            # Если устройство подключено локально, нельзя отключиться от него
            self.logger.info(f"Устройство {device_id} подключено локально, отключение не требуется")
            return True

    async def execute_command(
        self, 
        device_id: str, 
        command: List[str], 
        timeout: Optional[int] = None, 
        retries: Optional[int] = None
    ) -> Tuple[bool, str, str]:
        """
        Выполнение ADB-команды для конкретного устройства.
        
        Args:
            device_id: Идентификатор устройства.
            command: Список аргументов команды.
            timeout: Таймаут для команды в секундах (опционально).
            retries: Количество повторных попыток (опционально).
            
        Returns:
            Tuple[bool, str, str]: Успех, стандартный вывод, стандартный вывод ошибок.
        """
        if timeout is None:
            timeout = self.timeout
            
        if retries is None:
            retries = self.max_retries
        
        full_command = [self.adb_path, '-s', device_id] + command
        
        if self.debug:
            self.logger.debug(f"Выполнение команды: {' '.join(full_command)}")
        
        for attempt in range(retries):
            try:
                process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                    stdout_text = stdout.decode('utf-8', errors='replace')
                    stderr_text = stderr.decode('utf-8', errors='replace')
                    
                    if process.returncode == 0:
                        return True, stdout_text, stderr_text
                    
                    # Если устройство не найдено, прекращаем попытки
                    if 'device not found' in stderr_text or 'device \'' in stderr_text and '\' not found' in stderr_text:
                        self.logger.error(f"Устройство {device_id} не найдено")
                        return False, stdout_text, stderr_text
                    
                    self.logger.warning(f"Ошибка выполнения команды (попытка {attempt+1}/{retries}): {stderr_text}")
                    
                except asyncio.TimeoutError:
                    process.kill()
                    self.logger.warning(f"Таймаут при выполнении команды (попытка {attempt+1}/{retries})")
                    await asyncio.sleep(self.retry_interval)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Ошибка при выполнении команды: {e}")
                await asyncio.sleep(self.retry_interval)
                continue
                
            await asyncio.sleep(self.retry_interval)
        
        return False, "", f"Не удалось выполнить команду после {retries} попыток"

    async def shell_command(
        self, 
        device_id: str, 
        command: str, 
        timeout: Optional[int] = None, 
        retries: Optional[int] = None
    ) -> Tuple[bool, str, str]:
        """
        Выполнение shell-команды на устройстве.
        
        Args:
            device_id: Идентификатор устройства.
            command: Shell-команда.
            timeout: Таймаут для команды в секундах (опционально).
            retries: Количество повторных попыток (опционально).
            
        Returns:
            Tuple[bool, str, str]: Успех, стандартный вывод, стандартный вывод ошибок.
        """
        return await self.execute_command(device_id, ['shell', command], timeout, retries)

    async def push_file(self, device_id: str, local_path: str, remote_path: str) -> bool:
        """
        Отправка файла на устройство.
        
        Args:
            device_id: Идентификатор устройства.
            local_path: Локальный путь к файлу.
            remote_path: Удаленный путь для сохранения файла.
            
        Returns:
            bool: Успешна ли отправка файла.
        """
        try:
            success, stdout, stderr = await self.execute_command(
                device_id, ['push', local_path, remote_path]
            )
            
            if not success:
                self.logger.error(f"Ошибка при отправке файла на устройство {device_id}: {stderr}")
                return False
                
            self.logger.debug(f"Файл {local_path} успешно отправлен на устройство {device_id} в {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке файла: {e}")
            return False

    async def pull_file(self, device_id: str, remote_path: str, local_path: str) -> bool:
        """
        Получение файла с устройства.
        
        Args:
            device_id: Идентификатор устройства.
            remote_path: Удаленный путь к файлу.
            local_path: Локальный путь для сохранения файла.
            
        Returns:
            bool: Успешно ли получение файла.
        """
        try:
            success, stdout, stderr = await self.execute_command(
                device_id, ['pull', remote_path, local_path]
            )
            
            if not success:
                self.logger.error(f"Ошибка при получении файла с устройства {device_id}: {stderr}")
                return False
                
            self.logger.debug(f"Файл {remote_path} успешно получен с устройства {device_id} в {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении файла: {e}")
            return False

    async def take_screenshot(self, device_id: str, local_path: Optional[str] = None) -> Optional[str]:
        """
        Создание скриншота устройства.
        
        Args:
            device_id: Идентификатор устройства.
            local_path: Локальный путь для сохранения скриншота (опционально).
            
        Returns:
            Optional[str]: Путь к сохраненному скриншоту или None в случае ошибки.
        """
        try:
            # Генерация пути для скриншота, если он не указан
            if not local_path:
                # Определение директории для выходных файлов
                output_dir = os.path.join(os.getcwd(), 'screenshots', 'output')
                os.makedirs(output_dir, exist_ok=True)
                
                # Генерация имени файла на основе времени и ID устройства
                timestamp = int(time.time())
                safe_device_id = device_id.replace(':', '_').replace('.', '_')
                local_path = os.path.join(output_dir, f"screenshot_{safe_device_id}_{timestamp}.png")
            
            # Временный путь на устройстве
            remote_path = f"/sdcard/screenshot_{int(time.time())}.png"
            
            # Выполнение команды для создания скриншота
            success, stdout, stderr = await self.shell_command(
                device_id, f"screencap -p {remote_path}"
            )
            
            if not success:
                self.logger.error(f"Ошибка при создании скриншота на устройстве {device_id}: {stderr}")
                return None
            
            # Скачивание скриншота с устройства
            success = await self.pull_file(device_id, remote_path, local_path)
            
            if not success:
                self.logger.error(f"Ошибка при скачивании скриншота с устройства {device_id}")
                return None
            
            # Удаление временного файла на устройстве
            await self.shell_command(device_id, f"rm {remote_path}")
            
            self.logger.info(f"Скриншот устройства {device_id} сохранен в {local_path}")
            return local_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании скриншота: {e}")
            return None

    async def input_tap(self, device_id: str, x: int, y: int) -> bool:
        """
        Симуляция нажатия на экран.
        
        Args:
            device_id: Идентификатор устройства.
            x: Координата X.
            y: Координата Y.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            success, stdout, stderr = await self.shell_command(
                device_id, f"input tap {x} {y}"
            )
            
            if not success:
                self.logger.error(f"Ошибка при выполнении нажатия на {device_id} в координатах ({x}, {y}): {stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении нажатия: {e}")
            return False

    async def input_swipe(
        self, 
        device_id: str, 
        x1: int, 
        y1: int, 
        x2: int, 
        y2: int, 
        duration_ms: int = 500
    ) -> bool:
        """
        Симуляция свайпа на экране.
        
        Args:
            device_id: Идентификатор устройства.
            x1: Начальная координата X.
            y1: Начальная координата Y.
            x2: Конечная координата X.
            y2: Конечная координата Y.
            duration_ms: Продолжительность свайпа в миллисекундах.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            success, stdout, stderr = await self.shell_command(
                device_id, f"input swipe {x1} {y1} {x2} {y2} {duration_ms}"
            )
            
            if not success:
                self.logger.error(
                    f"Ошибка при выполнении свайпа на {device_id} "
                    f"от ({x1}, {y1}) до ({x2}, {y2}): {stderr}"
                )
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении свайпа: {e}")
            return False

    async def input_text(self, device_id: str, text: str) -> bool:
        """
        Ввод текста на устройстве.
        
        Args:
            device_id: Идентификатор устройства.
            text: Текст для ввода.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            # Экранирование специальных символов в тексте
            escaped_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
            
            success, stdout, stderr = await self.shell_command(
                device_id, f'input text "{escaped_text}"'
            )
            
            if not success:
                self.logger.error(f"Ошибка при вводе текста на {device_id}: {stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при вводе текста: {e}")
            return False

    async def input_keyevent(self, device_id: str, keycode: int) -> bool:
        """
        Отправка события клавиши на устройство.
        
        Args:
            device_id: Идентификатор устройства.
            keycode: Код клавиши (Android KeyEvent).
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            success, stdout, stderr = await self.shell_command(
                device_id, f"input keyevent {keycode}"
            )
            
            if not success:
                self.logger.error(f"Ошибка при отправке keyevent {keycode} на {device_id}: {stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке keyevent: {e}")
            return False

    async def restart_app(self, device_id: str, package_name: str) -> bool:
        """
        Перезапуск приложения на устройстве.
        
        Args:
            device_id: Идентификатор устройства.
            package_name: Имя пакета приложения.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            # Остановка приложения
            success1, stdout1, stderr1 = await self.shell_command(
                device_id, f"am force-stop {package_name}"
            )
            
            # Запуск приложения
            success2, stdout2, stderr2 = await self.shell_command(
                device_id, f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
            )
            
            if not success1 or not success2:
                self.logger.error(f"Ошибка при перезапуске {package_name} на {device_id}: {stderr1} {stderr2}")
                return False
                
            self.logger.debug(f"Приложение {package_name} успешно перезапущено на {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при перезапуске приложения: {e}")
            return False

    async def get_device_info(self, device_id: str) -> Dict[str, str]:
        """
        Получение информации об устройстве.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            Dict[str, str]: Словарь с информацией об устройстве.
        """
        info = {
            'id': device_id,
            'status': 'unknown',
            'model': 'unknown',
            'android_version': 'unknown',
            'screen_resolution': 'unknown'
        }
        
        try:
            # Проверка статуса устройства
            devices = await self.get_devices()
            for device in devices:
                if device['id'] == device_id:
                    info['status'] = device['state']
                    break
            
            # Если устройство не подключено, возвращаем базовую информацию
            if info['status'] != 'device':
                return info
            
            # Получение модели устройства
            success, stdout, stderr = await self.shell_command(
                device_id, "getprop ro.product.model"
            )
            if success:
                info['model'] = stdout.strip()
            
            # Получение версии Android
            success, stdout, stderr = await self.shell_command(
                device_id, "getprop ro.build.version.release"
            )
            if success:
                info['android_version'] = stdout.strip()
            
            # Получение разрешения экрана
            success, stdout, stderr = await self.shell_command(
                device_id, "wm size"
            )
            if success:
                # Парсинг вывода вида "Physical size: 1080x2340"
                match = re.search(r'Physical size: (\d+x\d+)', stdout)
                if match:
                    info['screen_resolution'] = match.group(1)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации об устройстве {device_id}: {e}")
            return info

    async def input_long_tap(
        self, 
        device_id: str, 
        x: int, 
        y: int, 
        duration_ms: int = 1000
    ) -> bool:
        """
        Симуляция длительного нажатия на экран.
        
        Args:
            device_id: Идентификатор устройства.
            x: Координата X.
            y: Координата Y.
            duration_ms: Продолжительность нажатия в миллисекундах.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        return await self.input_swipe(device_id, x, y, x, y, duration_ms)

    async def is_screen_on(self, device_id: str) -> bool:
        """
        Проверка, включен ли экран устройства.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            bool: Включен ли экран.
        """
        try:
            # Выполнение команды для проверки состояния экрана
            success, stdout, stderr = await self.shell_command(
                device_id, "dumpsys power | grep 'Display Power: state='"
            )
            
            if not success:
                self.logger.error(f"Ошибка при проверке состояния экрана на {device_id}: {stderr}")
                return False
            
            # Проверка результата
            if 'ON' in stdout:
                return True
            else:
                return False
            
        except Exception as e:
            self.logger.error(f"Ошибка при проверке состояния экрана: {e}")
            return False

    async def wake_up_device(self, device_id: str) -> bool:
        """
        Включение экрана устройства, если он выключен.
        
        Args:
            device_id: Идентификатор устройства.
            
        Returns:
            bool: Успешно ли выполнение команды.
        """
        try:
            # Проверка состояния экрана
            screen_on = await self.is_screen_on(device_id)
            
            if screen_on:
                return True
            
            # Включение экрана
            success, stdout, stderr = await self.shell_command(
                device_id, "input keyevent KEYCODE_WAKEUP"
            )
            
            if not success:
                self.logger.error(f"Ошибка при включении экрана на {device_id}: {stderr}")
                return False
            
            # Разблокировка устройства (свайп вверх)
            success, stdout, stderr = await self.shell_command(
                device_id, "wm size"
            )
            
            if success:
                # Парсинг разрешения экрана
                match = re.search(r'Physical size: (\d+)x(\d+)', stdout)
                if match:
                    width = int(match.group(1))
                    height = int(match.group(2))
                    
                    # Свайп вверх для разблокировки
                    await self.input_swipe(
                        device_id, 
                        width // 2, 
                        height * 3 // 4, 
                        width // 2, 
                        height // 4
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при включении экрана устройства: {e}")
            return False