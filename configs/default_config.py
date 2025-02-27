#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Базовая конфигурация для ADB Блюстакс Автоматизация.
Выполняет подключение к BlueStacks, запуск приложения и выполнение простых действий.
"""

# Импорт необходимых модулей
import os
import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Основная конфигурация
CONFIG = {
    # Название конфигурации
    'name': 'default_config',
    
    # Описание конфигурации
    'description': 'Базовая конфигурация для BlueStacks',
    
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
    
    # Список действий для выполнения
    'actions': [
        # Запуск приложения и очистка уведомлений
        {
            'type': 'restart_app',
            'package': 'com.launcher.brgame',
            'description': 'Запуск лаунчера BlueStacks',
            'wait_after': 3000
        },
        
        # Ожидание загрузки лаунчера
        {
            'type': 'wait_image',
            'template': 'home_icon.png',
            'description': 'Ожидание загрузки лаунчера',
            'timeout': 20,
            'wait_after': 1000
        },
        
        # Нажатие на иконку запуска приложения
        {
            'type': 'click_image',
            'template': 'app_icon.png',
            'description': 'Запуск приложения',
            'threshold': 0.8,
            'wait_after': 5000
        },
        
        # Ожидание загрузки приложения
        {
            'type': 'wait_image',
            'template': 'login_button.png',
            'description': 'Ожидание загрузки экрана входа',
            'timeout': 30,
            'wait_after': 1000
        },
        
        # Нажатие на кнопку входа
        {
            'type': 'click_image',
            'template': 'login_button.png',
            'description': 'Нажатие на кнопку входа',
            'threshold': 0.8,
            'wait_after': 2000
        },
        
        # Ввод логина
        {
            'type': 'click_image',
            'template': 'login_field.png',
            'description': 'Нажатие на поле логина',
            'threshold': 0.8,
            'wait_after': 1000
        },
        
        {
            'type': 'input_text',
            'text': 'test_user',
            'description': 'Ввод логина',
            'wait_after': 1000
        },
        
        # Ввод пароля
        {
            'type': 'click_image',
            'template': 'password_field.png',
            'description': 'Нажатие на поле пароля',
            'threshold': 0.8,
            'wait_after': 1000
        },
        
        {
            'type': 'input_text',
            'text': 'password123',
            'description': 'Ввод пароля',
            'wait_after': 1000
        },
        
        # Нажатие на кнопку подтверждения
        {
            'type': 'click_image',
            'template': 'confirm_button.png',
            'description': 'Нажатие на кнопку подтверждения',
            'threshold': 0.8,
            'wait_after': 5000
        },
        
        # Ожидание загрузки главного экрана
        {
            'type': 'wait_image',
            'template': 'main_screen.png',
            'description': 'Ожидание загрузки главного экрана',
            'timeout': 30,
            'wait_after': 1000
        },
        
        # Нажатие на кнопку меню
        {
            'type': 'click_image',
            'template': 'menu_button.png',
            'description': 'Нажатие на кнопку меню',
            'threshold': 0.8,
            'wait_after': 2000
        },
        
        # Нажатие на кнопку настроек
        {
            'type': 'click_image',
            'template': 'settings_button.png',
            'description': 'Нажатие на кнопку настроек',
            'threshold': 0.8,
            'wait_after': 3000
        },
        
        # Свайп вниз по экрану настроек
        {
            'type': 'swipe',
            'x1': 400,
            'y1': 800,
            'x2': 400,
            'y2': 300,
            'duration': 500,
            'description': 'Свайп вниз по экрану настроек',
            'wait_after': 1000
        },
        
        # Нажатие на кнопку выхода из аккаунта
        {
            'type': 'click_image',
            'template': 'logout_button.png',
            'description': 'Нажатие на кнопку выхода из аккаунта',
            'threshold': 0.8,
            'wait_after': 2000
        },
        
        # Нажатие на подтверждение выхода
        {
            'type': 'click_image',
            'template': 'confirm_logout.png',
            'description': 'Подтверждение выхода из аккаунта',
            'threshold': 0.8,
            'wait_after': 3000
        }
    ],
    
    # Шаги для выполнения
    'steps': [
        # Шаг 1: Перезапуск приложения
        {
            'name': 'restart_app',
            'description': 'Перезапуск лаунчера BlueStacks',
            'action': 'restart_app',
            'package': 'com.launcher.brgame'
        },
        
        # Шаг 2: Проверка состояния устройства
        {
            'name': 'check_device',
            'description': 'Проверка состояния устройства',
            'action': 'check_device_status'
        },
        
        # Шаг 3: Выполнение входа в приложение
        {
            'name': 'login',
            'description': 'Вход в приложение',
            'action': 'perform_login',
            'username': 'test_user',
            'password': 'password123'
        },
        
        # Шаг 4: Выполнение основных действий в приложении
        {
            'name': 'main_actions',
            'description': 'Основные действия в приложении',
            'action': 'perform_main_actions'
        },
        
        # Шаг 5: Выход из приложения
        {
            'name': 'logout',
            'description': 'Выход из приложения',
            'action': 'perform_logout'
        }
    ],
    
    # Включенные шаги (по умолчанию все)
    'enabled_steps': {
        'restart_app': True,
        'check_device': True,
        'login': True,
        'main_actions': True,
        'logout': True
    }
}

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
    logger.info(f"Инициализация конфигурации {CONFIG['name']} для устройства {device_id}")
    
    # Проверка, подключено ли устройство
    if not device_manager.device_connected(device_id):
        logger.error(f"Устройство {device_id} не подключено")
        return False
    
    # Проверка наличия каталога с шаблонами изображений
    templates_dir = os.path.join('screenshots', 'templates')
    if not os.path.exists(templates_dir) or not os.path.isdir(templates_dir):
        logger.warning(f"Каталог с шаблонами изображений не найден: {templates_dir}")
        logger.warning("Создайте каталог и добавьте в него шаблоны изображений")
        # Создание каталога
        os.makedirs(templates_dir, exist_ok=True)
    
    # Проверка наличия основных шаблонов изображений
    required_templates = [
        'home_icon.png',
        'app_icon.png',
        'login_button.png',
        'login_field.png',
        'password_field.png',
        'confirm_button.png',
        'main_screen.png',
        'menu_button.png',
        'settings_button.png',
        'logout_button.png',
        'confirm_logout.png'
    ]
    
    missing_templates = []
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if not os.path.exists(template_path):
            missing_templates.append(template)
    
    if missing_templates:
        logger.warning(f"Отсутствуют следующие шаблоны изображений: {', '.join(missing_templates)}")
        logger.warning("Добавьте отсутствующие шаблоны в каталог screenshots/templates")
    
    # Пробуждение устройства, если экран выключен
    if not device_manager.is_screen_on(device_id):
        logger.info("Пробуждение устройства...")
        if not device_manager.wake_up_device(device_id):
            logger.warning("Не удалось пробудить устройство")
    
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
    logger.info(f"Завершение конфигурации {CONFIG['name']} для устройства {device_id} (успех: {success})")
    
    # Создание финального скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        logger.info(f"Финальный скриншот сохранен: {screenshot_path}")
    
    # Проверка и сброс состояния устройства
    device_manager.update_device_action(device_id, None)

# Пользовательские функции для шагов
def restart_app(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Перезапуск приложения.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    package = kwargs.get('package', 'com.launcher.brgame')
    logger.info(f"Перезапуск приложения {package} на устройстве {device_id}")
    
    # Перезапуск приложения через ADB
    return device_manager.restart_app(device_id, package, f"Перезапуск {package}")

def check_device_status(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Проверка состояния устройства.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    logger.info(f"Проверка состояния устройства {device_id}")
    
    # Получение информации об устройстве
    info = device_manager.get_device_info(device_id)
    
    if info:
        logger.info(f"Модель устройства: {info.get('model', 'Неизвестно')}")
        logger.info(f"Версия Android: {info.get('android_version', 'Неизвестно')}")
        logger.info(f"Разрешение экрана: {info.get('screen_resolution', 'Неизвестно')}")
        
        # Создание скриншота
        screenshot_path = device_manager.take_screenshot(device_id)
        if screenshot_path:
            logger.info(f"Скриншот сохранен: {screenshot_path}")
        
        # Сброс ориентации экрана
        device_manager.execute_shell_command(
            device_id, 
            "settings put system accelerometer_rotation 0 && settings put system user_rotation 0"
        )
        
        return True
    else:
        logger.error("Не удалось получить информацию об устройстве")
        return False

def perform_login(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Выполнение входа в приложение.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    username = kwargs.get('username', 'test_user')
    password = kwargs.get('password', 'password123')
    
    logger.info(f"Выполнение входа в приложение с логином {username}")
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if not screenshot_path:
        logger.error("Не удалось создать скриншот")
        return False
    
    # Загрузка скриншота
    screenshot = image_processor.load_image(screenshot_path)
    if screenshot is None:
        logger.error("Не удалось загрузить скриншот")
        return False
    
    # Ожидание появления экрана входа
    login_found = False
    for attempt in range(5):
        # Создание скриншота
        screenshot_path = device_manager.take_screenshot(device_id)
        if not screenshot_path:
            logger.error("Не удалось создать скриншот")
            continue
        
        # Загрузка скриншота
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is None:
            logger.error("Не удалось загрузить скриншот")
            continue
        
        # Поиск кнопки входа
        login_button = image_processor.find_template(
            screenshot, 
            'login_button.png', 
            threshold=0.8
        )
        
        if login_button:
            login_found = True
            logger.info("Найден экран входа")
            
            # Нажатие на кнопку входа
            x, y = image_processor.get_template_center(login_button)
            device_manager.input_tap(device_id, x, y, "Нажатие на кнопку входа")
            time.sleep(2)
            break
        
        logger.debug(f"Ожидание экрана входа (попытка {attempt+1}/5)")
        time.sleep(2)
    
    if not login_found:
        logger.warning("Экран входа не найден, переход к вводу логина")
    
    # Ввод логина
    logger.info("Ввод логина")
    login_field_found = False
    
    # Поиск поля для ввода логина
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            login_field = image_processor.find_template(
                screenshot, 
                'login_field.png', 
                threshold=0.8
            )
            
            if login_field:
                login_field_found = True
                x, y = image_processor.get_template_center(login_field)
                
                # Нажатие на поле для ввода логина
                device_manager.input_tap(device_id, x, y, "Нажатие на поле логина")
                time.sleep(1)
                
                # Очистка поля ввода
                device_manager.execute_shell_command(
                    device_id, 
                    "input keyevent KEYCODE_MOVE_END && input keyevent --longpress KEYCODE_DEL"
                )
                time.sleep(0.5)
                
                # Ввод логина
                device_manager.input_text(device_id, username, "Ввод логина")
                time.sleep(1)
    
    if not login_field_found:
        logger.warning("Поле для ввода логина не найдено")
    
    # Ввод пароля
    logger.info("Ввод пароля")
    password_field_found = False
    
    # Поиск поля для ввода пароля
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            password_field = image_processor.find_template(
                screenshot, 
                'password_field.png', 
                threshold=0.8
            )
            
            if password_field:
                password_field_found = True
                x, y = image_processor.get_template_center(password_field)
                
                # Нажатие на поле для ввода пароля
                device_manager.input_tap(device_id, x, y, "Нажатие на поле пароля")
                time.sleep(1)
                
                # Очистка поля ввода
                device_manager.execute_shell_command(
                    device_id, 
                    "input keyevent KEYCODE_MOVE_END && input keyevent --longpress KEYCODE_DEL"
                )
                time.sleep(0.5)
                
                # Ввод пароля
                device_manager.input_text(device_id, password, "Ввод пароля")
                time.sleep(1)
    
    if not password_field_found:
        logger.warning("Поле для ввода пароля не найдено")
    
    # Нажатие на кнопку подтверждения
    logger.info("Нажатие на кнопку подтверждения")
    confirm_found = False
    
    # Поиск кнопки подтверждения
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            confirm_button = image_processor.find_template(
                screenshot, 
                'confirm_button.png', 
                threshold=0.8
            )
            
            if confirm_button:
                confirm_found = True
                x, y = image_processor.get_template_center(confirm_button)
                
                # Нажатие на кнопку подтверждения
                device_manager.input_tap(device_id, x, y, "Нажатие на кнопку подтверждения")
                time.sleep(5)
    
    if not confirm_found:
        logger.warning("Кнопка подтверждения не найдена")
        # Попытка нажатия клавиши Enter
        device_manager.execute_shell_command(device_id, "input keyevent KEYCODE_ENTER")
        time.sleep(5)
    
    # Ожидание загрузки главного экрана
    main_screen_found = False
    for attempt in range(6):  # 30 секунд (6 попыток по 5 секунд)
        # Создание скриншота
        screenshot_path = device_manager.take_screenshot(device_id)
        if not screenshot_path:
            logger.error("Не удалось создать скриншот")
            continue
        
        # Загрузка скриншота
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is None:
            logger.error("Не удалось загрузить скриншот")
            continue
        
        # Поиск главного экрана
        main_screen = image_processor.find_template(
            screenshot, 
            'main_screen.png', 
            threshold=0.7
        )
        
        if main_screen:
            main_screen_found = True
            logger.info("Главный экран найден, вход выполнен успешно")
            break
        
        logger.debug(f"Ожидание главного экрана (попытка {attempt+1}/6)")
        time.sleep(5)
    
    if not main_screen_found:
        logger.warning("Главный экран не найден после входа")
        return False
    
    return True

def perform_main_actions(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Выполнение основных действий в приложении.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    logger.info("Выполнение основных действий в приложении")
    
    # Нажатие на кнопку меню
    menu_found = False
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            menu_button = image_processor.find_template(
                screenshot, 
                'menu_button.png', 
                threshold=0.8
            )
            
            if menu_button:
                menu_found = True
                x, y = image_processor.get_template_center(menu_button)
                
                # Нажатие на кнопку меню
                device_manager.input_tap(device_id, x, y, "Нажатие на кнопку меню")
                time.sleep(2)
    
    if not menu_found:
        logger.warning("Кнопка меню не найдена")
    
    # Нажатие на кнопку настроек
    settings_found = False
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            settings_button = image_processor.find_template(
                screenshot, 
                'settings_button.png', 
                threshold=0.8
            )
            
            if settings_button:
                settings_found = True
                x, y = image_processor.get_template_center(settings_button)
                
                # Нажатие на кнопку настроек
                device_manager.input_tap(device_id, x, y, "Нажатие на кнопку настроек")
                time.sleep(3)
    
    if not settings_found:
        logger.warning("Кнопка настроек не найдена")
    
    # Выполнение свайпа по экрану
    logger.info("Выполнение свайпа по экрану")
    
    # Получение размеров экрана
    width, height = 1080, 1920  # По умолчанию
    
    # Попытка получения реальных размеров экрана
    screen_size_result = device_manager.execute_shell_command(device_id, "wm size")
    if screen_size_result[0]:
        # Парсинг вывода вида "Physical size: 1080x1920"
        output = screen_size_result[1]
        match = re.search(r'Physical size: (\d+)x(\d+)', output)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
    
    # Выполнение свайпа от центра нижней части экрана к центру верхней части
    device_manager.execute_shell_command(
        device_id, 
        f"input swipe {width//2} {height*3//4} {width//2} {height//4} 500",
        "Свайп по экрану"
    )
    time.sleep(1)
    
    return True

def perform_logout(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    """
    Выполнение выхода из приложения.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    """
    logger.info("Выполнение выхода из приложения")
    
    # Нажатие на кнопку выхода
    logout_found = False
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            logout_button = image_processor.find_template(
                screenshot, 
                'logout_button.png', 
                threshold=0.8
            )
            
            if logout_button:
                logout_found = True
                x, y = image_processor.get_template_center(logout_button)
                
                # Нажатие на кнопку выхода
                device_manager.input_tap(device_id, x, y, "Нажатие на кнопку выхода")
                time.sleep(2)
    
    if not logout_found:
        logger.warning("Кнопка выхода не найдена")
    
    # Подтверждение выхода
    confirm_found = False
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            confirm_logout = image_processor.find_template(
                screenshot, 
                'confirm_logout.png', 
                threshold=0.8
            )
            
            if confirm_logout:
                confirm_found = True
                x, y = image_processor.get_template_center(confirm_logout)
                
                # Нажатие на кнопку подтверждения выхода
                device_manager.input_tap(device_id, x, y, "Подтверждение выхода")
                time.sleep(3)
    
    if not confirm_found:
        logger.warning("Кнопка подтверждения выхода не найдена")
    
    # Проверка, что выход выполнен успешно
    logout_success = False
    
    # Создание скриншота
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            login_screen = image_processor.find_template(
                screenshot, 
                'login_button.png', 
                threshold=0.7
            )
            
            if login_screen:
                logout_success = True
                logger.info("Выход выполнен успешно, найден экран входа")
    
    if not logout_success:
        logger.warning("Не удалось подтвердить успешный выход из приложения")
    
    return True