#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль выполнения действий для ADB Блюстакс Автоматизация.
Обеспечивает выполнение действий и шагов конфигураций на устройствах.
"""

import os
import time
import asyncio
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union
import inspect
import concurrent.futures
from modules.image_processor import ImageProcessor


class ActionExecutor:
    """
    Класс для выполнения действий и шагов конфигураций на устройствах.
    """

    def __init__(
        self, 
        device_manager, 
        config_loader, 
        logger: logging.Logger, 
        ui
    ):
        """
        Инициализация исполнителя действий.
        
        Args:
            device_manager: Экземпляр менеджера устройств.
            config_loader: Экземпляр загрузчика конфигураций.
            logger: Логгер для записи событий.
            ui: Интерфейс пользователя для вывода информации.
        """
        self.device_manager = device_manager
        self.config_loader = config_loader
        self.logger = logger
        self.ui = ui
        
        # Создание обработчика изображений
        self.image_processor = ImageProcessor({}, logger)
        
        # Состояние выполнения
        self.running = False
        self.paused = False
        
        # Информация о выполняющихся конфигурациях
        self.running_configs = {}
        self.running_devices = set()
        
        # Блокировка для потокобезопасного доступа к состоянию
        self.state_lock = asyncio.Lock()
        
        # Событие для управления паузой
        self.resume_event = asyncio.Event()
        self.resume_event.set()  # По умолчанию не находится в режиме паузы

    async def execute_config(
        self, 
        device_id: str, 
        config_name: str, 
        device_logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        Выполнение конфигурации для устройства.
        
        Args:
            device_id: Идентификатор устройства.
            config_name: Имя конфигурации для выполнения.
            device_logger: Логгер для устройства (опционально).
            
        Returns:
            bool: Успешно ли выполнение конфигурации.
        """
        try:
            # Получение логгера для устройства, если он не передан
            if device_logger is None:
                device_logger = await self.device_manager.get_device_logger(device_id)
            
            # Установка флага выполнения
            async with self.state_lock:
                self.running = True
                self.running_configs[device_id] = config_name
                self.running_devices.add(device_id)
            
            # Получение названия устройства для отображения
            device_name = self.device_manager.devices.get(device_id, {}).get('name', device_id)
            
            # Вывод информации о начале выполнения
            self.ui.print_device_message(device_id, f"Начало выполнения конфигурации {config_name}", "INFO")
            device_logger.info(f"Начало выполнения конфигурации {config_name}")
            
            # Создание прогресс-бара для устройства
            self.ui.create_progress(device_id, f"Выполнение {config_name}", 100)
            
            # Валидация конфигурации
            if not self.config_loader.validate_config(config_name):
                error_msg = f"Ошибка: Конфигурация {config_name} не найдена или не валидна"
                self.ui.print_device_message(device_id, error_msg, "ERROR")
                device_logger.error(error_msg)
                self.ui.complete_progress(device_id, False)
                
                # Сброс флага выполнения
                async with self.state_lock:
                    if device_id in self.running_configs:
                        del self.running_configs[device_id]
                    self.running_devices.discard(device_id)
                
                return False
            
            # Загрузка конфигурации
            config_data = self.config_loader.get_loaded_config(config_name)
            if not config_data:
                error_msg = f"Ошибка: Не удалось загрузить конфигурацию {config_name}"
                self.ui.print_device_message(device_id, error_msg, "ERROR")
                device_logger.error(error_msg)
                self.ui.complete_progress(device_id, False)
                
                # Сброс флага выполнения
                async with self.state_lock:
                    if device_id in self.running_configs:
                        del self.running_configs[device_id]
                    self.running_devices.discard(device_id)
                
                return False
            
            # Получение модуля конфигурации
            config_module = config_data['module']
            config = config_data['config']
            
            # Проверка, подключено ли устройство
            if not await self.device_manager.device_connected(device_id):
                error_msg = f"Ошибка: Устройство {device_name} не подключено"
                self.ui.print_device_message(device_id, error_msg, "ERROR")
                device_logger.error(error_msg)
                self.ui.complete_progress(device_id, False)
                
                # Сброс флага выполнения
                async with self.state_lock:
                    if device_id in self.running_configs:
                        del self.running_configs[device_id]
                    self.running_devices.discard(device_id)
                
                return False
            
            # Выполнение инициализации, если она определена
            if hasattr(config_module, 'initialize'):
                device_logger.info("Выполнение инициализации...")
                self.ui.update_progress(device_id, 0, "Инициализация")
                
                try:
                    init_success = config_module.initialize(device_id, self.device_manager, self.image_processor, device_logger)
                    if not init_success:
                        error_msg = "Ошибка при инициализации конфигурации"
                        self.ui.print_device_message(device_id, error_msg, "ERROR")
                        device_logger.error(error_msg)
                        self.ui.complete_progress(device_id, False)
                        
                        # Сброс флага выполнения
                        async with self.state_lock:
                            if device_id in self.running_configs:
                                del self.running_configs[device_id]
                            self.running_devices.discard(device_id)
                        
                        return False
                except Exception as e:
                    error_msg = f"Исключение при инициализации конфигурации: {e}"
                    self.ui.print_device_message(device_id, error_msg, "ERROR")
                    device_logger.exception(error_msg)
                    self.ui.complete_progress(device_id, False)
                    
                    # Сброс флага выполнения
                    async with self.state_lock:
                        if device_id in self.running_configs:
                            del self.running_configs[device_id]
                        self.running_devices.discard(device_id)
                    
                    return False
            
            # Получение списка шагов
            steps = config.get('steps', [])
            if not steps:
                warning_msg = "Предупреждение: Список шагов пуст"
                self.ui.print_device_message(device_id, warning_msg, "WARNING")
                device_logger.warning(warning_msg)
                
                # Выполнение финализации, если она определена
                if hasattr(config_module, 'finalize'):
                    device_logger.info("Выполнение финализации...")
                    try:
                        config_module.finalize(device_id, self.device_manager, self.image_processor, device_logger, False)
                    except Exception as e:
                        device_logger.exception(f"Исключение при финализации конфигурации: {e}")
                
                self.ui.complete_progress(device_id, False)
                
                # Сброс флага выполнения
                async with self.state_lock:
                    if device_id in self.running_configs:
                        del self.running_configs[device_id]
                    self.running_devices.discard(device_id)
                
                return False
            
            # Получение словаря включенных шагов
            enabled_steps = config.get('enabled_steps', {})
            
            # Подсчет общего количества шагов для прогресс-бара
            total_steps = len(steps)
            steps_completed = 0
            
            # Статус успешности выполнения
            success = True
            
            # Выполнение каждого шага
            for i, step in enumerate(steps):
                # Проверка, если выполнение было остановлено
                if not self.running:
                    break
                
                # Ожидание снятия паузы, если она установлена
                await self.resume_event.wait()
                
                # Получение имени и описания шага
                step_name = step.get('name', f"Шаг {i+1}")
                step_description = step.get('description', step_name)
                
                # Проверка, включен ли шаг
                if step_name in enabled_steps and not enabled_steps[step_name]:
                    device_logger.info(f"Пропуск шага {step_name} (отключен)")
                    self.ui.update_progress(device_id, (i + 1) * 100 // total_steps, f"Пропуск: {step_description}")
                    steps_completed += 1
                    continue
                
                # Получение имени действия
                action_name = step.get('action')
                if not action_name:
                    error_msg = f"Ошибка в шаге {step_name}: Не указано действие"
                    self.ui.print_device_message(device_id, error_msg, "ERROR")
                    device_logger.error(error_msg)
                    success = False
                    break
                
                # Проверка наличия функции в модуле
                if not hasattr(config_module, action_name):
                    error_msg = f"Ошибка в шаге {step_name}: Функция {action_name} не найдена в модуле"
                    self.ui.print_device_message(device_id, error_msg, "ERROR")
                    device_logger.error(error_msg)
                    success = False
                    break
                
                # Получение функции
                action_func = getattr(config_module, action_name)
                
                # Проверка, что это действительно функция
                if not callable(action_func):
                    error_msg = f"Ошибка в шаге {step_name}: {action_name} не является функцией"
                    self.ui.print_device_message(device_id, error_msg, "ERROR")
                    device_logger.error(error_msg)
                    success = False
                    break
                
                # Вывод информации о выполнении шага
                device_logger.info(f"Выполнение шага {step_name}: {step_description}")
                self.ui.update_progress(device_id, i * 100 // total_steps, f"Шаг {i+1}/{total_steps}: {step_description}")
                self.ui.print_device_message(device_id, f"Выполнение: {step_description}", "INFO")
                
                # Обновление статуса устройства
                await self.device_manager.update_device_action(device_id, step_description)
                
                try:
                    # Выполнение действия
                    step_success = action_func(device_id, self.device_manager, self.image_processor, device_logger, **step)
                    
                    if not step_success:
                        error_msg = f"Ошибка в шаге {step_name}: Действие {action_name} завершилось с ошибкой"
                        self.ui.print_device_message(device_id, error_msg, "ERROR")
                        device_logger.error(error_msg)
                        success = False
                        break
                    
                    # Увеличение счетчика выполненных шагов
                    steps_completed += 1
                    
                except Exception as e:
                    error_msg = f"Исключение в шаге {step_name}: {e}"
                    self.ui.print_device_message(device_id, error_msg, "ERROR")
                    device_logger.exception(error_msg)
                    traceback.print_exc()
                    success = False
                    break
                
                # Обновление прогресса
                self.ui.update_progress(device_id, (i + 1) * 100 // total_steps, f"Выполнено: {step_description}")
            
            # Сброс статуса устройства
            await self.device_manager.update_device_action(device_id, None)
            
            # Выполнение финализации, если она определена
            if hasattr(config_module, 'finalize'):
                device_logger.info("Выполнение финализации...")
                try:
                    config_module.finalize(device_id, self.device_manager, self.image_processor, device_logger, success)
                except Exception as e:
                    device_logger.exception(f"Исключение при финализации конфигурации: {e}")
            
            # Вывод информации о завершении выполнения
            if success:
                device_logger.info(f"Выполнение конфигурации {config_name} успешно завершено")
                self.ui.print_device_message(device_id, f"Конфигурация {config_name} успешно выполнена", "INFO")
            else:
                device_logger.warning(f"Выполнение конфигурации {config_name} завершено с ошибками")
                self.ui.print_device_message(device_id, f"Конфигурация {config_name} выполнена с ошибками", "WARNING")
            
            # Завершение прогресс-бара
            self.ui.complete_progress(device_id, success)
            
            # Сброс флага выполнения
            async with self.state_lock:
                if device_id in self.running_configs:
                    del self.running_configs[device_id]
                self.running_devices.discard(device_id)
            
            return success
            
        except asyncio.CancelledError:
            # Обработка отмены задачи
            self.logger.info(f"Выполнение конфигурации {config_name} для устройства {device_id} отменено")
            
            # Сброс статуса устройства
            await self.device_manager.update_device_action(device_id, None)
            
            # Завершение прогресс-бара
            self.ui.complete_progress(device_id, False)
            
            # Сброс флага выполнения
            async with self.state_lock:
                if device_id in self.running_configs:
                    del self.running_configs[device_id]
                self.running_devices.discard(device_id)
            
            return False
            
        except Exception as e:
            # Обработка исключений
            error_msg = f"Критическая ошибка при выполнении конфигурации {config_name}: {e}"
            self.logger.exception(error_msg)
            if device_logger:
                device_logger.exception(error_msg)
            
            # Вывод сообщения об ошибке
            self.ui.print_device_message(device_id, error_msg, "ERROR")
            
            # Сброс статуса устройства
            await self.device_manager.update_device_action(device_id, None)
            
            # Завершение прогресс-бара
            self.ui.complete_progress(device_id, False)
            
            # Сброс флага выполнения
            async with self.state_lock:
                if device_id in self.running_configs:
                    del self.running_configs[device_id]
                self.running_devices.discard(device_id)
            
            return False

    async def stop_execution(self) -> None:
        """Остановка выполнения всех конфигураций."""
        self.logger.info("Остановка выполнения всех конфигураций")
        
        # Сброс флага выполнения
        async with self.state_lock:
            self.running = False
            self.paused = False
            
            # Сброс флага паузы
            self.resume_event.set()
        
        # Сброс статуса для всех устройств
        for device_id in list(self.running_devices):
            await self.device_manager.update_device_action(device_id, None)

    async def pause_execution(self) -> None:
        """Приостановка выполнения всех конфигураций."""
        self.logger.info("Приостановка выполнения всех конфигураций")
        
        # Установка флага паузы
        async with self.state_lock:
            if self.running:
                self.paused = True
                self.resume_event.clear()

    async def resume_execution(self) -> None:
        """Возобновление выполнения всех конфигураций."""
        self.logger.info("Возобновление выполнения всех конфигураций")
        
        # Сброс флага паузы
        async with self.state_lock:
            if self.running and self.paused:
                self.paused = False
                self.resume_event.set()

    async def is_paused(self) -> bool:
        """
        Проверка, находится ли выполнение в режиме паузы.
        
        Returns:
            bool: Находится ли выполнение в режиме паузы.
        """
        return self.paused

    async def get_running_configs(self) -> Dict[str, str]:
        """
        Получение словаря выполняющихся конфигураций.
        
        Returns:
            Dict[str, str]: Словарь в формате {device_id: config_name}.
        """
        return self.running_configs.copy()

    async def get_running_devices(self) -> List[str]:
        """
        Получение списка устройств, на которых выполняется автоматизация.
        
        Returns:
            List[str]: Список идентификаторов устройств.
        """
        return list(self.running_devices)

    async def execute_action(
        self, 
        device_id: str, 
        action: Dict[str, Any], 
        device_logger: Optional[logging.Logger] = None,
        config_name: Optional[str] = None
    ) -> bool:
        """
        Выполнение отдельного действия на устройстве.
        
        Args:
            device_id: Идентификатор устройства.
            action: Словарь с описанием действия.
            device_logger: Логгер для устройства (опционально).
            config_name: Имя конфигурации для контекста (опционально).
            
        Returns:
            bool: Успешно ли выполнение действия.
        """
        try:
            # Получение логгера для устройства, если он не передан
            if device_logger is None:
                device_logger = await self.device_manager.get_device_logger(device_id)
            
            # Проверка, подключено ли устройство
            if not await self.device_manager.device_connected(device_id):
                device_logger.error(f"Устройство {device_id} не подключено")
                return False
            
            # Получение типа действия
            action_type = action.get('type')
            if not action_type:
                device_logger.error("Не указан тип действия")
                return False
            
            # Получение описания действия
            description = action.get('description', f"Действие {action_type}")
            
            # Вывод информации о выполнении действия
            device_logger.info(f"Выполнение действия: {description}")
            
            # Обновление статуса устройства
            await self.device_manager.update_device_action(device_id, description)
            
            # Выполнение действия в зависимости от типа
            success = False
            
            if action_type == 'click_image':
                # Нажатие на изображение
                template = action.get('template')
                if not template:
                    device_logger.error("Не указан шаблон для нажатия")
                    return False
                
                # Создание скриншота
                screenshot_path = await self.device_manager.take_screenshot(device_id)
                if not screenshot_path:
                    device_logger.error("Не удалось создать скриншот")
                    return False
                
                # Загрузка скриншота
                screenshot = self.image_processor.load_image(screenshot_path)
                if screenshot is None:
                    device_logger.error("Не удалось загрузить скриншот")
                    return False
                
                # Поиск шаблона на скриншоте
                threshold = action.get('threshold', 0.7)
                template_result = self.image_processor.find_template(
                    screenshot, 
                    template, 
                    threshold=threshold
                )
                
                if template_result:
                    # Получение координат центра шаблона
                    x, y = self.image_processor.get_template_center(template_result)
                    
                    # Нажатие на найденные координаты
                    success = await self.device_manager.input_tap(device_id, x, y, f"Нажатие на {template}")
                    
                    if success:
                        device_logger.info(f"Успешное нажатие на шаблон {template} в координатах ({x}, {y})")
                    else:
                        device_logger.error(f"Ошибка при нажатии на шаблон {template}")
                else:
                    device_logger.warning(f"Шаблон {template} не найден на скриншоте")
            
            elif action_type == 'input_text':
                # Ввод текста
                text = action.get('text', '')
                if not text:
                    device_logger.warning("Пустая строка для ввода")
                
                # Ввод текста на устройстве
                success = await self.device_manager.input_text(device_id, text, f"Ввод текста")
                
                if success:
                    device_logger.info(f"Успешный ввод текста: {text}")
                else:
                    device_logger.error(f"Ошибка при вводе текста: {text}")
            
            elif action_type == 'wait_image':
                # Ожидание появления изображения
                template = action.get('template')
                if not template:
                    device_logger.error("Не указан шаблон для ожидания")
                    return False
                
                timeout = action.get('timeout', 30)
                threshold = action.get('threshold', 0.7)
                
                # Начальное время
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    # Ожидание снятия паузы, если она установлена
                    await self.resume_event.wait()
                    
                    # Создание скриншота
                    screenshot_path = await self.device_manager.take_screenshot(device_id)
                    if not screenshot_path:
                        device_logger.error("Не удалось создать скриншот")
                        await asyncio.sleep(1)
                        continue
                    
                    # Загрузка скриншота
                    screenshot = self.image_processor.load_image(screenshot_path)
                    if screenshot is None:
                        device_logger.error("Не удалось загрузить скриншот")
                        await asyncio.sleep(1)
                        continue
                    
                    # Поиск шаблона на скриншоте
                    template_result = self.image_processor.find_template(
                        screenshot, 
                        template, 
                        threshold=threshold
                    )
                    
                    if template_result:
                        device_logger.info(f"Шаблон {template} найден на скриншоте")
                        success = True
                        break
                    
                    device_logger.debug(f"Ожидание шаблона {template}... ({int(time.time() - start_time)}/{timeout}с)")
                    await asyncio.sleep(1)
                
                if not success:
                    device_logger.warning(f"Превышено время ожидания шаблона {template}")
            
            elif action_type == 'swipe':
                # Свайп по экрану
                x1 = action.get('x1', 0)
                y1 = action.get('y1', 0)
                x2 = action.get('x2', 0)
                y2 = action.get('y2', 0)
                duration = action.get('duration', 500)
                
                if x1 == 0 and y1 == 0 and x2 == 0 and y2 == 0:
                    device_logger.error("Не указаны координаты для свайпа")
                    return False
                
                # Выполнение свайпа
                success = await self.device_manager.execute_adb_command(
                    device_id, 
                    ['shell', f'input swipe {x1} {y1} {x2} {y2} {duration}'],
                    f"Свайп от ({x1}, {y1}) до ({x2}, {y2})"
                )[0]
                
                if success:
                    device_logger.info(f"Успешный свайп от ({x1}, {y1}) до ({x2}, {y2})")
                else:
                    device_logger.error(f"Ошибка при свайпе от ({x1}, {y1}) до ({x2}, {y2})")
            
            elif action_type == 'keyevent':
                # Отправка события клавиши
                keycode = action.get('keycode')
                if not keycode:
                    device_logger.error("Не указан код клавиши")
                    return False
                
                # Выполнение нажатия клавиши
                success = await self.device_manager.execute_adb_command(
                    device_id, 
                    ['shell', f'input keyevent {keycode}'],
                    f"Нажатие клавиши {keycode}"
                )[0]
                
                if success:
                    device_logger.info(f"Успешное нажатие клавиши {keycode}")
                else:
                    device_logger.error(f"Ошибка при нажатии клавиши {keycode}")
            
            elif action_type == 'sleep':
                # Пауза выполнения
                duration = action.get('duration', 1)
                
                device_logger.info(f"Пауза на {duration} секунд")
                await asyncio.sleep(duration)
                success = True
            
            elif action_type == 'restart_app':
                # Перезапуск приложения
                package = action.get('package')
                if not package:
                    device_logger.error("Не указан пакет приложения")
                    return False
                
                # Перезапуск приложения
                success = await self.device_manager.restart_app(device_id, package, f"Перезапуск приложения {package}")
                
                if success:
                    device_logger.info(f"Успешный перезапуск приложения {package}")
                else:
                    device_logger.error(f"Ошибка при перезапуске приложения {package}")
            
            elif action_type == 'shell_command':
                # Выполнение shell-команды
                command = action.get('command')
                if not command:
                    device_logger.error("Не указана команда")
                    return False
                
                # Выполнение команды
                result = await self.device_manager.execute_shell_command(
                    device_id, 
                    command,
                    f"Выполнение команды: {command}"
                )
                
                success = result[0]
                if success:
                    device_logger.info(f"Успешное выполнение команды: {command}")
                    device_logger.debug(f"Результат: {result[1]}")
                else:
                    device_logger.error(f"Ошибка при выполнении команды: {command}")
                    device_logger.debug(f"Ошибка: {result[2]}")
            
            elif action_type == 'tap':
                # Нажатие на координаты
                x = action.get('x', 0)
                y = action.get('y', 0)
                
                if x == 0 and y == 0:
                    device_logger.error("Не указаны координаты для нажатия")
                    return False
                
                # Выполнение нажатия
                success = await self.device_manager.input_tap(device_id, x, y, f"Нажатие на ({x}, {y})")
                
                if success:
                    device_logger.info(f"Успешное нажатие на координаты ({x}, {y})")
                else:
                    device_logger.error(f"Ошибка при нажатии на координаты ({x}, {y})")
            
            else:
                device_logger.error(f"Неизвестный тип действия: {action_type}")
            
            # Сброс статуса устройства
            await self.device_manager.update_device_action(device_id, None)
            
            # Пауза после действия
            wait_after = action.get('wait_after', 0)
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            
            return success
            
        except asyncio.CancelledError:
            # Обработка отмены задачи
            self.logger.info(f"Выполнение действия для устройства {device_id} отменено")
            
            # Сброс статуса устройства
            await self.device_manager.update_device_action(device_id, None)
            
            return False
            
        except Exception as e:
            # Обработка исключений
            error_msg = f"Ошибка при выполнении действия: {e}"
            self.logger.exception(error_msg)
            if device_logger:
                device_logger.exception(error_msg)
            
            # Сброс статуса устройства
            await self.device_manager.update_device_action(device_id, None)
            
            return False