#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль загрузки конфигураций для ADB Блюстакс Автоматизация.
Обеспечивает загрузку и обработку пользовательских конфигураций для автоматизации.
"""

import os
import sys
import yaml
import importlib.util
import inspect
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable


class ConfigLoader:
    """
    Класс для загрузки и обработки пользовательских конфигураций.
    """

    def __init__(self, configs_dir: str, logger: logging.Logger):
        """
        Инициализация загрузчика конфигураций.
        
        Args:
            configs_dir: Директория с конфигурациями.
            logger: Логгер для записи событий.
        """
        self.configs_dir = configs_dir
        self.logger = logger
        
        # Словарь загруженных конфигов
        self.loaded_configs = {}
        
        # Базовые классы для проверки конфигов
        self.base_classes = {}
        
        # Создание директории для конфигураций, если она не существует
        os.makedirs(configs_dir, exist_ok=True)

    def scan_configs(self) -> List[str]:
        """
        Сканирование директории для поиска файлов конфигураций.
        
        Returns:
            List[str]: Список имен найденных конфигов.
        """
        config_files = []
        
        try:
            # Получение списка всех файлов Python в директории конфигураций
            for item in os.listdir(self.configs_dir):
                if item.endswith('.py') and not item.startswith('__'):
                    config_name = item[:-3]  # Удаление расширения .py
                    config_files.append(config_name)
            
            self.logger.info(f"Найдено {len(config_files)} файлов конфигураций")
            return config_files
            
        except Exception as e:
            self.logger.exception(f"Ошибка при сканировании директории конфигураций: {e}")
            return []

    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Загрузка конфигурации из файла.
        
        Args:
            config_name: Имя конфигурации (без расширения).
            
        Returns:
            Optional[Dict[str, Any]]: Конфигурация или None в случае ошибки.
        """
        try:
            # Проверка, загружен ли конфиг уже
            if config_name in self.loaded_configs:
                return self.loaded_configs[config_name]
            
            # Формирование полного пути к файлу
            config_path = os.path.join(self.configs_dir, f"{config_name}.py")
            
            # Проверка существования файла
            if not os.path.exists(config_path):
                self.logger.error(f"Файл конфигурации не найден: {config_path}")
                return None
            
            # Загрузка модуля
            spec = importlib.util.spec_from_file_location(config_name, config_path)
            if spec is None or spec.loader is None:
                self.logger.error(f"Не удалось загрузить спецификацию модуля: {config_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Проверка наличия основной конфигурации
            if not hasattr(module, 'CONFIG'):
                self.logger.error(f"В файле {config_path} не найдена переменная CONFIG")
                return None
            
            # Получение конфигурации
            config = module.CONFIG
            
            # Проверка структуры конфигурации
            if not isinstance(config, dict):
                self.logger.error(f"Конфигурация в файле {config_path} должна быть словарем")
                return None
            
            # Сохранение конфигурации
            self.loaded_configs[config_name] = {
                'name': config_name,
                'path': config_path,
                'module': module,
                'config': config
            }
            
            self.logger.info(f"Конфигурация {config_name} успешно загружена")
            return self.loaded_configs[config_name]
            
        except Exception as e:
            self.logger.exception(f"Ошибка при загрузке конфигурации {config_name}: {e}")
            return None

    def load_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Загрузка всех доступных конфигураций.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь загруженных конфигураций.
        """
        # Очистка словаря загруженных конфигов
        self.loaded_configs = {}
        
        # Сканирование директории для поиска файлов конфигураций
        config_names = self.scan_configs()
        
        # Загрузка каждой конфигурации
        for config_name in config_names:
            self.load_config(config_name)
        
        self.logger.info(f"Загружено {len(self.loaded_configs)} конфигураций")
        return self.loaded_configs

    def is_config_loaded(self, config_name: str) -> bool:
        """
        Проверка, загружена ли конфигурация.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            bool: Загружена ли конфигурация.
        """
        return config_name in self.loaded_configs

    def get_loaded_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение загруженной конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            Optional[Dict[str, Any]]: Конфигурация или None, если она не загружена.
        """
        return self.loaded_configs.get(config_name)

    def get_config_value(
        self, 
        config_name: str, 
        key: str, 
        default: Any = None
    ) -> Any:
        """
        Получение значения из конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            key: Ключ для получения значения.
            default: Значение по умолчанию, если ключ не найден.
            
        Returns:
            Any: Значение из конфигурации или значение по умолчанию.
        """
        try:
            # Проверка, загружена ли конфигурация
            if not self.is_config_loaded(config_name):
                if not self.load_config(config_name):
                    return default
            
            # Получение конфигурации
            config = self.loaded_configs[config_name]['config']
            
            # Получение значения
            return config.get(key, default)
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении значения {key} из конфигурации {config_name}: {e}")
            return default

    def get_config_actions(self, config_name: str) -> List[Dict[str, Any]]:
        """
        Получение списка действий из конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            List[Dict[str, Any]]: Список действий.
        """
        try:
            # Получение действий из конфигурации
            actions = self.get_config_value(config_name, 'actions', [])
            
            # Проверка типа действий
            if not isinstance(actions, list):
                self.logger.error(f"Действия в конфигурации {config_name} должны быть списком")
                return []
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении действий из конфигурации {config_name}: {e}")
            return []

    def get_config_steps(self, config_name: str) -> List[Dict[str, Any]]:
        """
        Получение списка шагов из конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            List[Dict[str, Any]]: Список шагов.
        """
        try:
            # Получение шагов из конфигурации
            steps = self.get_config_value(config_name, 'steps', [])
            
            # Проверка типа шагов
            if not isinstance(steps, list):
                self.logger.error(f"Шаги в конфигурации {config_name} должны быть списком")
                return []
            
            return steps
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении шагов из конфигурации {config_name}: {e}")
            return []

    def get_config_enabled_steps(self, config_name: str) -> Dict[str, bool]:
        """
        Получение словаря включенных шагов из конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            Dict[str, bool]: Словарь включенных шагов.
        """
        try:
            # Получение словаря включенных шагов из конфигурации
            enabled_steps = self.get_config_value(config_name, 'enabled_steps', {})
            
            # Проверка типа словаря
            if not isinstance(enabled_steps, dict):
                self.logger.error(f"Словарь включенных шагов в конфигурации {config_name} должен быть словарем")
                return {}
            
            return enabled_steps
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении словаря включенных шагов из конфигурации {config_name}: {e}")
            return {}

    def get_config_function(
        self, 
        config_name: str, 
        function_name: str
    ) -> Optional[Callable]:
        """
        Получение функции из модуля конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            function_name: Имя функции.
            
        Returns:
            Optional[Callable]: Функция или None, если она не найдена.
        """
        try:
            # Проверка, загружена ли конфигурация
            if not self.is_config_loaded(config_name):
                if not self.load_config(config_name):
                    return None
            
            # Получение модуля конфигурации
            module = self.loaded_configs[config_name]['module']
            
            # Проверка наличия функции в модуле
            if not hasattr(module, function_name):
                self.logger.error(f"Функция {function_name} не найдена в модуле {config_name}")
                return None
            
            # Получение функции
            function = getattr(module, function_name)
            
            # Проверка, что это действительно функция
            if not callable(function):
                self.logger.error(f"{function_name} в модуле {config_name} не является функцией")
                return None
            
            return function
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении функции {function_name} из модуля {config_name}: {e}")
            return None

    def call_config_function(
        self, 
        config_name: str, 
        function_name: str, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Вызов функции из модуля конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            function_name: Имя функции.
            *args: Позиционные аргументы для функции.
            **kwargs: Именованные аргументы для функции.
            
        Returns:
            Any: Результат выполнения функции или None в случае ошибки.
        """
        try:
            # Получение функции
            function = self.get_config_function(config_name, function_name)
            
            if function is None:
                return None
            
            # Вызов функции
            return function(*args, **kwargs)
            
        except Exception as e:
            self.logger.exception(f"Ошибка при вызове функции {function_name} из модуля {config_name}: {e}")
            return None

    def get_config_next_config(self, config_name: str) -> Optional[str]:
        """
        Получение имени следующей конфигурации для выполнения.
        
        Args:
            config_name: Имя текущей конфигурации.
            
        Returns:
            Optional[str]: Имя следующей конфигурации или None.
        """
        try:
            # Получение имени следующей конфигурации
            next_config = self.get_config_value(config_name, 'next_config', None)
            
            # Если следующая конфигурация указана, проверяем ее существование
            if next_config:
                if not os.path.exists(os.path.join(self.configs_dir, f"{next_config}.py")):
                    self.logger.warning(f"Следующая конфигурация {next_config} не найдена")
                    return None
            
            return next_config
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении следующей конфигурации из {config_name}: {e}")
            return None

    def validate_config(self, config_name: str) -> bool:
        """
        Проверка корректности конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            bool: Корректна ли конфигурация.
        """
        try:
            # Проверка, загружена ли конфигурация
            if not self.is_config_loaded(config_name):
                if not self.load_config(config_name):
                    return False
            
            # Получение конфигурации
            config = self.loaded_configs[config_name]['config']
            
            # Список обязательных полей
            required_fields = ['actions', 'steps']
            
            # Проверка наличия обязательных полей
            for field in required_fields:
                if field not in config:
                    self.logger.error(f"В конфигурации {config_name} отсутствует обязательное поле {field}")
                    return False
            
            # Проверка формата действий
            actions = config['actions']
            if not isinstance(actions, list):
                self.logger.error(f"Действия в конфигурации {config_name} должны быть списком")
                return False
            
            # Проверка формата шагов
            steps = config['steps']
            if not isinstance(steps, list):
                self.logger.error(f"Шаги в конфигурации {config_name} должны быть списком")
                return False
            
            # Проверка формата словаря включенных шагов
            if 'enabled_steps' in config and not isinstance(config['enabled_steps'], dict):
                self.logger.error(f"Словарь включенных шагов в конфигурации {config_name} должен быть словарем")
                return False
            
            # Проверка корректности имени следующей конфигурации
            if 'next_config' in config and config['next_config']:
                next_config = config['next_config']
                if not os.path.exists(os.path.join(self.configs_dir, f"{next_config}.py")):
                    self.logger.warning(f"Следующая конфигурация {next_config} не найдена")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при проверке конфигурации {config_name}: {e}")
            return False

    def validate_all_configs(self) -> Dict[str, bool]:
        """
        Проверка корректности всех загруженных конфигураций.
        
        Returns:
            Dict[str, bool]: Словарь результатов проверки для каждой конфигурации.
        """
        results = {}
        
        # Загрузка всех конфигураций
        configs = self.load_all_configs()
        
        # Проверка каждой конфигурации
        for config_name in configs:
            results[config_name] = self.validate_config(config_name)
        
        return results

    def create_config_template(self, config_name: str) -> bool:
        """
        Создание шаблона конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            bool: Успешно ли создан шаблон.
        """
        try:
            # Формирование полного пути к файлу
            config_path = os.path.join(self.configs_dir, f"{config_name}.py")
            
            # Проверка существования файла
            if os.path.exists(config_path):
                self.logger.warning(f"Файл конфигурации уже существует: {config_path}")
                return False
            
            # Шаблон конфигурации
            template = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
Конфигурация для ADB Блюстакс Автоматизация.
Описание: Шаблон конфигурации
\"\"\"

# Импорт необходимых модулей
import os
import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Основная конфигурация
CONFIG = {
    # Название конфигурации
    'name': '{config_name}',
    
    # Описание конфигурации
    'description': 'Шаблон конфигурации',
    
    # Версия конфигурации
    'version': '1.0.0',
    
    # Автор конфигурации
    'author': 'Admin',
    
    # Имя следующей конфигурации для выполнения (опционально)
    'next_config': None,
    
    # Настройки выполнения
    'settings': {{
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
    }},
    
    # Список действий для выполнения
    'actions': [
        # Пример действия 1: Нажатие на изображение
        {{
            'type': 'click_image',
            'template': 'button_template.png',
            'description': 'Нажатие на кнопку',
            'max_attempts': 3,
            'wait_after': 1000
        }},
        
        # Пример действия 2: Ввод текста
        {{
            'type': 'input_text',
            'text': 'Hello, World!',
            'description': 'Ввод текста',
            'wait_after': 500
        }},
        
        # Пример действия 3: Ожидание изображения
        {{
            'type': 'wait_image',
            'template': 'loading_complete.png',
            'description': 'Ожидание завершения загрузки',
            'timeout': 10,
            'wait_after': 1000
        }}
    ],
    
    # Шаги для выполнения
    'steps': [
        # Шаг 1: Перезапуск приложения
        {{
            'name': 'restart_app',
            'description': 'Перезапуск приложения',
            'action': 'restart_app',
            'package': 'com.example.app'
        }},
        
        # Шаг 2: Выполнение действий
        {{
            'name': 'perform_actions',
            'description': 'Выполнение действий',
            'action': 'perform_actions',
            'actions': [0, 1, 2]  # Индексы действий из списка 'actions'
        }}
    ],
    
    # Включенные шаги (по умолчанию все)
    'enabled_steps': {{
        'restart_app': True,
        'perform_actions': True
    }}
}}

# Функция инициализации, вызывается перед выполнением конфигурации
def initialize(device_id: str, device_manager, image_processor, logger: logging.Logger) -> bool:
    \"\"\"
    Инициализация перед выполнением конфигурации.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        
    Returns:
        bool: Успешна ли инициализация.
    \"\"\"
    logger.info(f"Инициализация конфигурации {{CONFIG['name']}} для устройства {{device_id}}")
    return True

# Функция завершения, вызывается после выполнения конфигурации
def finalize(device_id: str, device_manager, image_processor, logger: logging.Logger, success: bool) -> None:
    \"\"\"
    Завершение после выполнения конфигурации.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        success: Успешно ли выполнение конфигурации.
    \"\"\"
    logger.info(f"Завершение конфигурации {{CONFIG['name']}} для устройства {{device_id}} (успех: {{success}})")

# Пользовательские функции для шагов
def restart_app(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    \"\"\"
    Перезапуск приложения.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    \"\"\"
    package = kwargs.get('package', 'com.example.app')
    logger.info(f"Перезапуск приложения {{package}} на устройстве {{device_id}}")
    
    # Перезапуск приложения через ADB
    return device_manager.restart_app(device_id, package, f"Перезапуск {{package}}")

def perform_actions(device_id: str, device_manager, image_processor, logger: logging.Logger, **kwargs) -> bool:
    \"\"\"
    Выполнение списка действий.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        **kwargs: Дополнительные аргументы.
        
    Returns:
        bool: Успешно ли выполнен шаг.
    \"\"\"
    # Получение списка индексов действий для выполнения
    action_indices = kwargs.get('actions', [])
    
    if not action_indices:
        logger.warning("Список действий пуст")
        return False
    
    logger.info(f"Выполнение {{len(action_indices)}} действий на устройстве {{device_id}}")
    
    # Выполнение каждого действия из списка
    for index in action_indices:
        if index < 0 or index >= len(CONFIG['actions']):
            logger.warning(f"Некорректный индекс действия: {{index}}")
            continue
        
        action = CONFIG['actions'][index]
        action_type = action.get('type')
        description = action.get('description', f"Действие {{index}}")
        
        logger.info(f"Выполнение действия: {{description}}")
        
        # Обновление статуса устройства
        device_manager.update_device_action(device_id, description)
        
        # Выполнение действия в зависимости от типа
        success = False
        
        if action_type == 'click_image':
            # Нажатие на изображение
            template = action.get('template')
            max_attempts = action.get('max_attempts', CONFIG['settings']['max_action_attempts'])
            
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
            
            # Поиск шаблона на скриншоте
            template_result = image_processor.find_template(
                screenshot, 
                template, 
                threshold=CONFIG['settings']['image_match_threshold']
            )
            
            if template_result:
                # Получение координат центра шаблона
                x, y = image_processor.get_template_center(template_result)
                
                # Нажатие на найденные координаты
                success = device_manager.input_tap(device_id, x, y, f"Нажатие на {{template}}")
            else:
                logger.warning(f"Шаблон {{template}} не найден на скриншоте")
        
        elif action_type == 'input_text':
            # Ввод текста
            text = action.get('text', '')
            
            # Ввод текста на устройстве
            success = device_manager.input_text(device_id, text, f"Ввод текста")
        
        elif action_type == 'wait_image':
            # Ожидание появления изображения
            template = action.get('template')
            timeout = action.get('timeout', CONFIG['settings']['wait_timeout'])
            
            # Начальное время
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Создание скриншота
                screenshot_path = device_manager.take_screenshot(device_id)
                if not screenshot_path:
                    logger.error("Не удалось создать скриншот")
                    time.sleep(1)
                    continue
                
                # Загрузка скриншота
                screenshot = image_processor.load_image(screenshot_path)
                if screenshot is None:
                    logger.error("Не удалось загрузить скриншот")
                    time.sleep(1)
                    continue
                
                # Поиск шаблона на скриншоте
                template_result = image_processor.find_template(
                    screenshot, 
                    template, 
                    threshold=CONFIG['settings']['image_match_threshold']
                )
                
                if template_result:
                    logger.info(f"Шаблон {{template}} найден на скриншоте")
                    success = True
                    break
                
                logger.debug(f"Ожидание шаблона {{template}}... ({{int(time.time() - start_time)}}/{{timeout}}с)")
                time.sleep(1)
            
            if not success:
                logger.warning(f"Превышено время ожидания шаблона {{template}}")
        
        else:
            logger.warning(f"Неизвестный тип действия: {{action_type}}")
        
        # Сброс статуса устройства
        device_manager.update_device_action(device_id, None)
        
        # Пауза после действия
        wait_after = action.get('wait_after', CONFIG['settings']['action_interval'])
        if wait_after > 0:
            time.sleep(wait_after / 1000)
        
        # Прерывание выполнения действий при неудаче
        if not success:
            logger.error(f"Не удалось выполнить действие: {{description}}")
            return False
    
    return True
"""
            
            # Заполнение шаблона
            template = template.format(config_name=config_name)
            
            # Запись шаблона в файл
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(template)
            
            self.logger.info(f"Шаблон конфигурации {config_name} создан: {config_path}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Ошибка при создании шаблона конфигурации {config_name}: {e}")
            return False

    def reload_config(self, config_name: str) -> bool:
        """
        Перезагрузка конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            bool: Успешна ли перезагрузка.
        """
        try:
            # Удаление конфигурации из словаря
            if config_name in self.loaded_configs:
                del self.loaded_configs[config_name]
            
            # Загрузка конфигурации
            if self.load_config(config_name):
                self.logger.info(f"Конфигурация {config_name} успешно перезагружена")
                return True
            else:
                self.logger.error(f"Не удалось перезагрузить конфигурацию {config_name}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Ошибка при перезагрузке конфигурации {config_name}: {e}")
            return False

    def get_config_dependencies(self, config_name: str) -> List[str]:
        """
        Получение списка зависимостей конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            List[str]: Список имен конфигураций, от которых зависит данная конфигурация.
        """
        try:
            # Получение зависимостей из конфигурации
            dependencies = self.get_config_value(config_name, 'dependencies', [])
            
            # Проверка типа зависимостей
            if not isinstance(dependencies, list):
                self.logger.error(f"Зависимости в конфигурации {config_name} должны быть списком")
                return []
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении зависимостей из конфигурации {config_name}: {e}")
            return []

    def check_config_dependencies(self, config_name: str) -> bool:
        """
        Проверка наличия всех зависимостей конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            bool: Доступны ли все зависимости.
        """
        try:
            # Получение списка зависимостей
            dependencies = self.get_config_dependencies(config_name)
            
            if not dependencies:
                return True
            
            # Проверка наличия каждой зависимости
            for dependency in dependencies:
                if not os.path.exists(os.path.join(self.configs_dir, f"{dependency}.py")):
                    self.logger.error(f"Зависимость {dependency} для конфигурации {config_name} не найдена")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при проверке зависимостей конфигурации {config_name}: {e}")
            return False

    def get_config_info(self, config_name: str) -> Dict[str, Any]:
        """
        Получение информации о конфигурации.
        
        Args:
            config_name: Имя конфигурации.
            
        Returns:
            Dict[str, Any]: Информация о конфигурации.
        """
        try:
            # Получение основной информации
            info = {
                'name': config_name,
                'description': self.get_config_value(config_name, 'description', ''),
                'version': self.get_config_value(config_name, 'version', '1.0.0'),
                'author': self.get_config_value(config_name, 'author', 'Unknown'),
                'steps_count': len(self.get_config_steps(config_name)),
                'actions_count': len(self.get_config_actions(config_name)),
                'next_config': self.get_config_next_config(config_name),
                'dependencies': self.get_config_dependencies(config_name),
                'valid': self.validate_config(config_name)
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о конфигурации {config_name}: {e}")
            return {'name': config_name, 'error': str(e)}