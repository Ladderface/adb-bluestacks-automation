#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Конфигурация автоматизации для BlueStacks.
Реализует многоэтапный процесс с поиском изображений, кликами и вводом текста.
"""

import os
import time
import logging
import random
import re
import glob
from typing import Dict, List, Any, Optional, Tuple, Union

# Основная конфигурация
CONFIG = {
    # Название конфигурации
    'name': 'automation_config',
    
    # Описание конфигурации
    'description': 'Многоэтапная автоматизация для BlueStacks',
    
    # Версия конфигурации
    'version': '1.0.0',
    
    # Автор конфигурации
    'author': 'Admin',
    
    # Имя следующей конфигурации для выполнения (опционально)
    'next_config': None,
    
    # Настройки выполнения
    'settings': {
        # Интервал между действиями в миллисекундах
        'action_interval': 500,
        
        # Максимальное количество попыток для каждого действия
        'max_action_attempts': 5,
        
        # Пауза между попытками в миллисекундах
        'retry_delay': 2000,
        
        # Время ожидания после каждого клика в миллисекундах
        'click_delay': 1000,
        
        # Порог совпадения изображений (от 0.0 до 1.0)
        'image_match_threshold': 0.7,
        
        # Максимальное время ожидания появления изображения в секундах
        'wait_timeout': 30
    },
    
    # Дополнительные настройки для текущей конфигурации
    'custom_settings': {
        # Приложения для перезапуска
        'restart_apps': [
            'com.br.top',
            'com.launcher.brgame'
        ],
        
        # Координаты для длительного клика в этапе 6
        'long_tap_coordinates': {
            'x': 320,
            'y': 320
        },
        
        # Координаты для дополнительного клика в этапе 10
        'additional_click_coordinates': {
            'x': 834,
            'y': 101
        },
        
        # Текст для ввода в этапе 4
        'input_text': 'NaftaliN1337228',
        
        # Максимальное количество перезапусков
        'max_restarts': 3,
        
        # Удалять временные скриншоты после анализа
        'delete_temp_screenshots': True
    },
    
    # Шаблоны изображений для каждого этапа
    'templates': {
        'click_image_1': 'tpl1729712561481.png',
        'click_image_2': 'tpl1729713570074.png',
        'restart_check': 'tpl1730041404533.png',
        'click_image_3': 'tpl1729759399717.png',
        'click_image_4': 'tpl1729760259340.png',
        'click_image_5': 'tpl1729760963933.png',
        'click_image_6': 'tpl1729761655306.png',
        'click_image_7': 'tpl1729762328309.png',
        'click_image_8': 'tpl1730957533790.png',
        'always_wait': '1337.png'
    },
    
    # Шаги для выполнения
    'steps': [
        # Шаг 0: Перезапуск приложений
        {
            'name': 'restart_apps',
            'description': 'Перезапуск приложений',
            'action': 'restart_applications'
        },
        
        # Шаг 1: Click Image 1
        {
            'name': 'click_image_1',
            'description': 'Поиск и клик по изображению 1',
            'action': 'find_and_click_image',
            'template': 'click_image_1'
        },
        
        # Шаг 2: Click Image 2
        {
            'name': 'click_image_2',
            'description': 'Поиск и клик по изображению 2',
            'action': 'find_and_click_image',
            'template': 'click_image_2',
            'check_restart': True
        },
        
        # Шаг 3: Click Image 3
        {
            'name': 'click_image_3',
            'description': 'Поиск и клик по изображению 3',
            'action': 'find_and_click_image',
            'template': 'click_image_3'
        },
        
        # Шаг 4: Input Text
        {
            'name': 'input_text',
            'description': 'Ввод текста',
            'action': 'input_text'
        },
        
        # Шаг 5: Click Image 4
        {
            'name': 'click_image_4',
            'description': 'Поиск и клик по изображению 4',
            'action': 'find_and_click_image',
            'template': 'click_image_4',
            'press_enter_if_not_found': True
        },
        
        # Шаг 6: Click Image 5 и длительный клик
        {
            'name': 'click_image_5',
            'description': 'Поиск изображения 5 и длительный клик',
            'action': 'find_image_and_long_tap',
            'template': 'click_image_5'
        },
        
        # Шаг 7: Click Image 6
        {
            'name': 'click_image_6',
            'description': 'Поиск и клик по изображению 6',
            'action': 'find_and_click_image',
            'template': 'click_image_6'
        },
        
        # Шаг 8: Click Image 7
        {
            'name': 'click_image_7',
            'description': 'Поиск и клик по изображению 7',
            'action': 'find_and_click_image',
            'template': 'click_image_7'
        },
        
        # Шаг 9: Always Wait
        {
            'name': 'always_wait',
            'description': 'Ожидание и клик по специальному изображению',
            'action': 'always_wait_for_image',
            'template': 'always_wait'
        },
        
        # Шаг 10: Additional Click
        {
            'name': 'additional_click',
            'description': 'Поиск изображения 8 и дополнительный клик',
            'action': 'additional_click',
            'template': 'click_image_8'
        }
    ],
    
    # Включенные шаги (по умолчанию все)
    'enabled_steps': {
        'restart_apps': True,
        'click_image_1': True,
        'click_image_2': True,
        'click_image_3': True,
        'input_text': True,
        'click_image_4': True,
        'click_image_5': True,
        'click_image_6': True,
        'click_image_7': True,
        'always_wait': True,
        'additional_click': True
    }
}

# Счетчик перезапусков
restart_count = 0

# Список временных скриншотов для удаления
temp_screenshots = []

# Функция инициализации, вызывается перед выполнением конфигурации
def initialize(device_id: str, device_manager, image_processor, logger: logging.Logger) -> bool:
    """
    Инициализация перед выполнением конфигурации.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        
    Returns:
        bool: Успешна ли инициализация.
    """
    global restart_count, temp_screenshots
    
    logger.info(f"Инициализация конфигурации {CONFIG['name']} для устройства {device_id}")
    
    # Сброс счетчика перезапусков
    restart_count = 0
    
    # Очистка списка временных скриншотов
    temp_screenshots = []
    
    # Проверка, подключено ли устройство
    if not device_manager.device_connected(device_id):
        logger.error(f"Устройство {device_id} не подключено")
        return False
    
    # Проверка наличия шаблонов изображений
    templates_dir = os.path.join('screenshots', 'templates')
    
    templates = CONFIG['templates']
    missing_templates = []
    
    for key, template_name in templates.items():
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            missing_templates.append(template_name)
    
    if missing_templates:
        logger.warning(f"Отсутствуют следующие шаблоны изображений: {', '.join(missing_templates)}")
        logger.warning("Добавьте отсутствующие шаблоны в каталог screenshots/templates")
        # Несмотря на отсутствие некоторых шаблонов, продолжаем выполнение
    
    logger.info("Инициализация успешно завершена")
    return True

# Функция завершения, вызывается после выполнения конфигурации
def finalize(device_id: str, device_manager, image_processor, logger: logging.Logger, success: bool) -> None:
    """
    Завершение после выполнения конфигурации.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        success: Успешно ли выполнение конфигурации.
    """
    global restart_count, temp_screenshots
    
    logger.info(f"Завершение конфигурации {CONFIG['name']} для устройства {device_id}")
    
    # Удаление временных скриншотов
    if CONFIG['custom_settings'].get('delete_temp_screenshots', True):
        logger.info(f"Удаление {len(temp_screenshots)} временных скриншотов")
        for screenshot_path in temp_screenshots:
            try:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    logger.debug(f"Удален временный скриншот: {screenshot_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении скриншота {screenshot_path}: {e}")
    
    # Сброс счетчика перезапусков
    restart_count = 0
    
    # Проверка и сброс состояния устройства
    device_manager.update_device_action(device_id, None)
    
    logger.info(f"Выполнение конфигурации {'успешно завершено' if success else 'завершено с ошибками'}")

# Пользовательские функции для шагов
def restart_applications(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Перезапуск приложений.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    # Получение списка приложений для перезапуска
    apps = CONFIG['custom_settings'].get('restart_apps', [])
    if not apps:
        logger.warning("Список приложений для перезапуска пуст")
        return True
    
    logger.info(f"Перезапуск приложений: {', '.join(apps)}")
    
    # Перезапуск каждого приложения
    for app in apps:
        # Остановка приложения
        logger.info(f"Остановка приложения {app}")
        stop_result = device_manager.execute_shell_command(
            device_id, 
            f"am force-stop {app}",
            f"Остановка {app}"
        )
        
        if not stop_result[0]:
            logger.warning(f"Не удалось остановить приложение {app}: {stop_result[2]}")
        
        # Запуск приложения
        logger.info(f"Запуск приложения {app}")
        start_result = device_manager.execute_shell_command(
            device_id, 
            f"monkey -p {app} -c android.intent.category.LAUNCHER 1",
            f"Запуск {app}"
        )
        
        if not start_result[0]:
            logger.warning(f"Не удалось запустить приложение {app}: {start_result[2]}")
        
        # Небольшая пауза между перезапусками
        time.sleep(1)
    
    # Ожидание запуска приложений
    logger.info("Ожидание запуска приложений")
    time.sleep(3)
    
    return True

def find_and_click_image(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Поиск изображения на экране и клик по нему.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    global restart_count, temp_screenshots
    
    # Получение шаблона из параметров
    template_key = kwargs.get('template')
    if not template_key or template_key not in CONFIG['templates']:
        logger.error(f"Некорректный ключ шаблона: {template_key}")
        return False
    
    template_name = CONFIG['templates'][template_key]
    check_restart = kwargs.get('check_restart', False)
    press_enter_if_not_found = kwargs.get('press_enter_if_not_found', False)
    
    logger.info(f"Поиск изображения {template_name} на экране")
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if not screenshot_path:
        logger.error("Не удалось создать скриншот")
        return False
    
    # Добавление скриншота в список временных
    temp_screenshots.append(screenshot_path)
    
    # Загрузка скриншота
    screenshot = image_processor.load_image(screenshot_path)
    if screenshot is None:
        logger.error("Не удалось загрузить скриншот")
        return False
    
    # Поиск шаблона на скриншоте
    template_result = image_processor.find_template(
        screenshot, 
        template_name, 
        threshold=CONFIG['settings']['image_match_threshold']
    )
    
    if template_result:
        # Получение координат центра шаблона
        x, y = image_processor.get_template_center(template_result)
        
        logger.info(f"Изображение {template_name} найдено, координаты: ({x}, {y})")
        
        # Нажатие на найденные координаты
        click_success = device_manager.input_tap(device_id, x, y, f"Нажатие на {template_name}")
        
        if not click_success:
            logger.error(f"Не удалось выполнить нажатие на {template_name}")
            return False
        
        # Пауза после клика
        time.sleep(CONFIG['settings']['click_delay'] / 1000)
        
        # Проверка необходимости перезапуска (только для этапа 2)
        if check_restart:
            logger.info("Проверка необходимости перезапуска")
            
            # Создание нового скриншота для проверки
            restart_screenshot_path = device_manager.take_screenshot(device_id)
            if restart_screenshot_path:
                # Добавление скриншота в список временных
                temp_screenshots.append(restart_screenshot_path)
                
                restart_screenshot = image_processor.load_image(restart_screenshot_path)
                if restart_screenshot is not None:
                    # Поиск изображения для перезапуска
                    restart_template = CONFIG['templates']['restart_check']
                    restart_result = image_processor.find_template(
                        restart_screenshot, 
                        restart_template, 
                        threshold=CONFIG['settings']['image_match_threshold']
                    )
                    
                    if restart_result:
                        logger.info("Обнаружено изображение для перезапуска")
                        
                        # Проверка счетчика перезапусков
                        max_restarts = CONFIG['custom_settings'].get('max_restarts', 3)
                        
                        if restart_count < max_restarts:
                            restart_count += 1
                            logger.info(f"Перезапуск ({restart_count}/{max_restarts})")
                            # Имитация перезапуска (в реальном сценарии тут мог бы быть код для перезапуска)
                            return False  # Возвращаем False для перезапуска процесса
                        else:
                            logger.warning(f"Достигнуто максимальное количество перезапусков ({max_restarts})")
        
        return True
    else:
        logger.warning(f"Изображение {template_name} не найдено на скриншоте")
        
        # Нажатие клавиши Enter, если изображение не найдено и это указано в параметрах
        if press_enter_if_not_found:
            logger.info("Нажатие клавиши Enter, так как изображение не найдено")
            enter_result = device_manager.execute_shell_command(
                device_id, 
                "input keyevent KEYCODE_ENTER",
                "Нажатие клавиши Enter"
            )
            
            if not enter_result[0]:
                logger.error("Не удалось нажать клавишу Enter")
                return False
            
            # Пауза после нажатия Enter
            time.sleep(CONFIG['settings']['click_delay'] / 1000)
            
            return True  # Считаем шаг успешным, даже если изображение не найдено
        
        return False

def input_text(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Ввод текста.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    # Получение текста для ввода
    text = kwargs.get('text', CONFIG['custom_settings'].get('input_text', ''))
    if not text:
        logger.warning("Текст для ввода не указан")
        return False
    
    logger.info(f"Ввод текста: {text}")
    
    # Очистка поля ввода (последовательные нажатия Backspace)
    logger.info("Очистка поля ввода")
    for _ in range(30):  # Достаточно много нажатий для очистки поля
        backspace_result = device_manager.execute_shell_command(
            device_id, 
            "input keyevent KEYCODE_DEL",
            "Нажатие клавиши Backspace"
        )
        
        if not backspace_result[0]:
            logger.warning("Не удалось нажать клавишу Backspace")
            break
    
    # Небольшая пауза после очистки
    time.sleep(0.5)
    
    # Ввод текста
    input_result = device_manager.input_text(device_id, text, "Ввод текста")
    if not input_result:
        logger.error(f"Не удалось ввести текст: {text}")
        return False
    
    # Нажатие клавиши Enter после ввода текста
    logger.info("Нажатие клавиши Enter после ввода текста")
    enter_result = device_manager.execute_shell_command(
        device_id, 
        "input keyevent KEYCODE_ENTER",
        "Нажатие клавиши Enter"
    )
    
    if not enter_result[0]:
        logger.error("Не удалось нажать клавишу Enter")
        return False
    
    # Пауза после ввода текста
    time.sleep(CONFIG['settings']['click_delay'] / 1000)
    
    return True

def find_image_and_long_tap(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Поиск изображения и выполнение длительного нажатия.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    global temp_screenshots
    
    # Получение шаблона из параметров
    template_key = kwargs.get('template')
    if not template_key or template_key not in CONFIG['templates']:
        logger.error(f"Некорректный ключ шаблона: {template_key}")
        return False
    
    template_name = CONFIG['templates'][template_key]
    
    # Координаты для длительного нажатия
    x = CONFIG['custom_settings']['long_tap_coordinates']['x']
    y = CONFIG['custom_settings']['long_tap_coordinates']['y']
    
    logger.info(f"Поиск изображения {template_name} на экране")
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if not screenshot_path:
        logger.error("Не удалось создать скриншот")
        return False
    
    # Добавление скриншота в список временных
    temp_screenshots.append(screenshot_path)
    
    # Загрузка скриншота
    screenshot = image_processor.load_image(screenshot_path)
    if screenshot is None:
        logger.error("Не удалось загрузить скриншот")
        return False
    
    # Поиск шаблона на скриншоте
    template_result = image_processor.find_template(
        screenshot, 
        template_name, 
        threshold=CONFIG['settings']['image_match_threshold']
    )
    
    if template_result:
        logger.info(f"Изображение {template_name} найдено")
        
        # Выполнение длительного нажатия по заданным координатам
        logger.info(f"Выполнение длительного нажатия по координатам ({x}, {y})")
        
        # Используем swipe с одинаковыми координатами для имитации длительного нажатия
        long_tap_result = device_manager.execute_shell_command(
            device_id, 
            f"input swipe {x} {y} {x} {y} 1000",  # 1000 мс = 1 секунда
            "Длительное нажатие"
        )
        
        if not long_tap_result[0]:
            logger.error("Не удалось выполнить длительное нажатие")
            return False
        
        # Пауза после длительного нажатия
        time.sleep(1)
        
        # Поиск и клик по изображению после длительного нажатия
        logger.info("Поиск изображения 8 после длительного нажатия")
        
        # Получение шаблона для поиска
        click_8_template = CONFIG['templates']['click_image_8']
        
        # Максимальное количество попыток поиска
        max_attempts = 5
        
        for attempt in range(max_attempts):
            # Создание нового скриншота для поиска
            search_screenshot_path = device_manager.take_screenshot(device_id)
            if not search_screenshot_path:
                logger.error("Не удалось создать скриншот для поиска")
                continue
            
            # Добавление скриншота в список временных
            temp_screenshots.append(search_screenshot_path)
            
            # Загрузка скриншота
            search_screenshot = image_processor.load_image(search_screenshot_path)
            if search_screenshot is None:
                logger.error("Не удалось загрузить скриншот для поиска")
                continue
            
            # Поиск шаблона на скриншоте
            search_result = image_processor.find_template(
                search_screenshot, 
                click_8_template, 
                threshold=CONFIG['settings']['image_match_threshold']
            )
            
            if search_result:
                # Получение координат центра шаблона
                x, y = image_processor.get_template_center(search_result)
                
                logger.info(f"Изображение {click_8_template} найдено, координаты: ({x}, {y})")
                
                # Нажатие на найденные координаты
                click_success = device_manager.input_tap(device_id, x, y, f"Нажатие на {click_8_template}")
                
                if not click_success:
                    logger.error(f"Не удалось выполнить нажатие на {click_8_template}")
                    continue
                
                # Пауза после клика
                time.sleep(CONFIG['settings']['click_delay'] / 1000)
                
                # Успешное выполнение шага
                logger.info(f"Успешный поиск и клик по изображению {click_8_template} (попытка {attempt+1})")
                return True
            else:
                logger.warning(f"Изображение {click_8_template} не найдено (попытка {attempt+1}/{max_attempts})")
                time.sleep(1)  # Пауза перед следующей попыткой
        
        # Если после всех попыток изображение не найдено
        logger.warning(f"Изображение {click_8_template} не найдено после {max_attempts} попыток")
        return False
    else:
        logger.warning(f"Изображение {template_name} не найдено на скриншоте")
        return False

def always_wait_for_image(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Постоянное ожидание и клик по изображению.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    global temp_screenshots
    
    # Получение шаблона из параметров
    template_key = kwargs.get('template')
    if not template_key or template_key not in CONFIG['templates']:
        logger.error(f"Некорректный ключ шаблона: {template_key}")
        return False
    
    template_name = CONFIG['templates'][template_key]
    
    logger.info(f"Ожидание появления изображения {template_name}")
    
    # Максимальное количество попыток
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        # Создание скриншота
        screenshot_path = device_manager.take_screenshot(device_id)
        if not screenshot_path:
            logger.error("Не удалось создать скриншот")
            attempt += 1
            time.sleep(1)
            continue
        
        # Добавление скриншота в список временных
        temp_screenshots.append(screenshot_path)
        
        # Загрузка скриншота
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is None:
            logger.error("Не удалось загрузить скриншот")
            attempt += 1
            time.sleep(1)
            continue
        
        # Поиск шаблона на скриншоте
        template_result = image_processor.find_template(
            screenshot, 
            template_name, 
            threshold=CONFIG['settings']['image_match_threshold']
        )
        
        if template_result:
            # Получение координат центра шаблона
            x, y = image_processor.get_template_center(template_result)
            
            logger.info(f"Изображение {template_name} найдено, координаты: ({x}, {y})")
            
            # Ожидание перед кликом
            time.sleep(1)
            
            # Нажатие на найденные координаты
            click_success = device_manager.input_tap(device_id, x, y, f"Нажатие на {template_name}")
            
            if not click_success:
                logger.error(f"Не удалось выполнить нажатие на {template_name}")
                attempt += 1
                time.sleep(1)
                continue
            
            # Пауза после клика
            time.sleep(CONFIG['settings']['click_delay'] / 1000)
            
            # Проверка, исчезло ли изображение после клика
            check_screenshot_path = device_manager.take_screenshot(device_id)
            if check_screenshot_path:
                # Добавление скриншота в список временных
                temp_screenshots.append(check_screenshot_path)
                
                check_screenshot = image_processor.load_image(check_screenshot_path)
                if check_screenshot is not None:
                    check_result = image_processor.find_template(
                        check_screenshot, 
                        template_name, 
                        threshold=CONFIG['settings']['image_match_threshold']
                    )
                    
                    if not check_result:
                        logger.info(f"Изображение {template_name} исчезло после клика")
                        return True
            
            logger.info(f"Изображение {template_name} все еще присутствует, продолжение")
        else:
            logger.info(f"Изображение {template_name} не найдено, переход к следующему шагу")
            return True
        
        attempt += 1
    
    logger.warning(f"Достигнуто максимальное количество попыток ({max_attempts}) для ожидания {template_name}")
    return True  # Считаем шаг успешным, даже если достигнут лимит попыток

def additional_click(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Поиск изображения и дополнительный клик по заданным координатам.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    global temp_screenshots
    
    # Получение шаблона из параметров
    template_key = kwargs.get('template')
    if not template_key or template_key not in CONFIG['templates']:
        logger.error(f"Некорректный ключ шаблона: {template_key}")
        return False
    
    template_name = CONFIG['templates'][template_key]
    
    # Координаты для дополнительного клика
    x = CONFIG['custom_settings']['additional_click_coordinates']['x']
    y = CONFIG['custom_settings']['additional_click_coordinates']['y']
    
    logger.info(f"Поиск изображения {template_name} для дополнительного клика")
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if not screenshot_path:
        logger.error("Не удалось создать скриншот")
        return False
    
    # Добавление скриншота в список временных
    temp_screenshots.append(screenshot_path)
    
    # Загрузка скриншота
    screenshot = image_processor.load_image(screenshot_path)
    if screenshot is None:
        logger.error("Не удалось загрузить скриншот")
        return False
    
    # Поиск шаблона на скриншоте
    template_result = image_processor.find_template(
        screenshot, 
        template_name, 
        threshold=CONFIG['settings']['image_match_threshold']
    )
    
    if template_result:
        logger.info(f"Изображение {template_name} найдено, выполнение дополнительного клика")
        
        # Выполнение длительного нажатия по заданным координатам
        logger.info(f"Выполнение длительного нажатия по координатам ({x}, {y})")
        
        # Используем swipe с одинаковыми координатами для имитации длительного нажатия
        long_tap_result = device_manager.execute_shell_command(
            device_id, 
            f"input swipe {x} {y} {x} {y} 1000",  # 1000 мс = 1 секунда
            "Длительное нажатие"
        )
        
        if not long_tap_result[0]:
            logger.error("Не удалось выполнить длительное нажатие")
            return False
        
        # Пауза после длительного нажатия
        time.sleep(1)
        
        return True
    else:
        logger.info(f"Изображение {template_name} не найдено, пропуск дополнительного клика")
        return True  # Считаем шаг успешным, даже если изображение не найдено