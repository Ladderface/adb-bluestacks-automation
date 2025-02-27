# Руководство по созданию конфигураций

## Содержание
1. [Введение](#введение)
2. [Структура конфигурационного файла](#структура-конфигурационного-файла)
3. [Основные компоненты конфигурации](#основные-компоненты-конфигурации)
4. [Типы действий](#типы-действий)
5. [Создание шагов](#создание-шагов)
6. [Функции инициализации и завершения](#функции-инициализации-и-завершения)
7. [Работа с изображениями](#работа-с-изображениями)
8. [Передача параметров](#передача-параметров)
9. [Цепочки конфигураций](#цепочки-конфигураций)
10. [Примеры конфигураций](#примеры-конфигураций)
11. [Советы и рекомендации](#советы-и-рекомендации)

## Введение

Конфигурационные файлы в ADB Блюстакс Автоматизация представляют собой Python-модули, которые описывают последовательность действий для автоматизации работы с эмуляторами BlueStacks. 

С помощью конфигураций вы можете:
- Автоматизировать вход в приложения
- Выполнять повторяющиеся действия
- Настраивать разные сценарии для разных устройств
- Создавать цепочки автоматизации

Все конфигурационные файлы размещаются в директории `configs/`.

## Структура конфигурационного файла

Стандартная структура конфигурационного файла выглядит следующим образом:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Описание конфигурации
"""

# Импорт необходимых модулей
import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple

# Основная конфигурация в виде словаря
CONFIG = {
    'name': 'имя_конфигурации',
    'description': 'Описание конфигурации',
    'version': '1.0.0',
    'author': 'Автор',
    'next_config': None,
    'settings': { ... },
    'actions': [ ... ],
    'steps': [ ... ],
    'enabled_steps': { ... }
}

# Функция инициализации
def initialize(device_id, device_manager, image_processor, logger):
    # Код инициализации
    return True

# Функция завершения
def finalize(device_id, device_manager, image_processor, logger, success):
    # Код завершения
    pass

# Пользовательские функции для шагов
def step_function1(device_id, device_manager, image_processor, logger, **kwargs):
    # Код функции
    return True

def step_function2(device_id, device_manager, image_processor, logger, **kwargs):
    # Код функции
    return True
```

## Основные компоненты конфигурации

### Словарь CONFIG

Словарь `CONFIG` содержит все параметры и настройки конфигурации:

- `name` - Имя конфигурации
- `description` - Описание конфигурации
- `version` - Версия конфигурации
- `author` - Автор конфигурации
- `next_config` - Имя следующей конфигурации для выполнения (опционально)
- `settings` - Настройки выполнения
- `actions` - Список отдельных действий
- `steps` - Список шагов для выполнения
- `enabled_steps` - Словарь включенных шагов

### Настройки (settings)

Словарь `settings` содержит параметры выполнения конфигурации:

```python
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
}
```

## Типы действий

Словарь `actions` содержит список отдельных действий, которые могут быть выполнены на устройстве. Каждое действие представляет собой словарь с параметрами:

### 1. click_image - Нажатие на изображение

```python
{
    'type': 'click_image',
    'template': 'button.png',           # Имя файла шаблона
    'description': 'Нажатие на кнопку', # Описание действия
    'threshold': 0.8,                   # Порог совпадения (опционально)
    'wait_after': 1000                  # Ожидание после действия в мс (опционально)
}
```

### 2. input_text - Ввод текста

```python
{
    'type': 'input_text',
    'text': 'Текст для ввода',         # Текст для ввода
    'description': 'Ввод текста',      # Описание действия
    'wait_after': 500                  # Ожидание после действия в мс (опционально)
}
```

### 3. wait_image - Ожидание появления изображения

```python
{
    'type': 'wait_image',
    'template': 'loading_complete.png',   # Имя файла шаблона
    'description': 'Ожидание загрузки',   # Описание действия
    'timeout': 30,                        # Таймаут в секундах (опционально)
    'threshold': 0.7,                     # Порог совпадения (опционально)
    'wait_after': 1000                    # Ожидание после действия в мс (опционально)
}
```

### 4. swipe - Свайп по экрану

```python
{
    'type': 'swipe',
    'x1': 100,                         # Начальная координата X
    'y1': 500,                         # Начальная координата Y
    'x2': 100,                         # Конечная координата X
    'y2': 200,                         # Конечная координата Y
    'duration': 500,                   # Длительность свайпа в мс
    'description': 'Свайп вверх',      # Описание действия
    'wait_after': 1000                 # Ожидание после действия в мс (опционально)
}
```

### 5. keyevent - Отправка события клавиши

```python
{
    'type': 'keyevent',
    'keycode': 'KEYCODE_ENTER',         # Код клавиши
    'description': 'Нажатие Enter',     # Описание действия
    'wait_after': 500                   # Ожидание после действия в мс (опционально)
}
```

### 6. sleep - Пауза

```python
{
    'type': 'sleep',
    'duration': 5,                     # Длительность паузы в секундах
    'description': 'Ожидание 5 секунд', # Описание действия
    'wait_after': 0                     # Ожидание после действия в мс (опционально)
}
```

### 7. restart_app - Перезапуск приложения

```python
{
    'type': 'restart_app',
    'package': 'com.example.app',       # Имя пакета приложения
    'description': 'Перезапуск приложения', # Описание действия
    'wait_after': 3000                  # Ожидание после действия в мс (опционально)
}
```

### 8. shell_command - Выполнение shell-команды

```python
{
    'type': 'shell_command',
    'command': 'am force-stop com.example.app', # Shell-команда
    'description': 'Остановка приложения',      # Описание действия
    'wait_after': 1000                          # Ожидание после действия в мс (опционально)
}
```

### 9. tap - Нажатие на координаты

```python
{
    'type': 'tap',
    'x': 500,                          # Координата X
    'y': 700,                          # Координата Y
    'description': 'Нажатие на координаты', # Описание действия
    'wait_after': 1000                 # Ожидание после действия в мс (опционально)
}
```

## Создание шагов

Шаги (`steps`) - это более высокоуровневые компоненты автоматизации, которые могут содержать несколько действий или вызывать пользовательские функции. Каждый шаг представляет собой словарь с параметрами:

```python
{
    'name': 'login',                 # Имя шага
    'description': 'Вход в приложение', # Описание шага
    'action': 'perform_login',       # Имя функции для выполнения
    'username': 'user',              # Дополнительные параметры для функции
    'password': 'pass123'
}
```

Имя функции в параметре `action` должно соответствовать имени функции, определенной в конфигурационном файле.

Для включения или отключения отдельных шагов используется словарь `enabled_steps`:

```python
'enabled_steps': {
    'restart_app': True,
    'login': True,
    'main_actions': False,  # Этот шаг будет пропущен
    'logout': True
}
```

## Функции инициализации и завершения

### Функция initialize

Вызывается перед выполнением конфигурации:

```python
def initialize(device_id, device_manager, image_processor, logger):
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
    logger.info(f"Инициализация для устройства {device_id}")
    
    # Проверки и подготовка
    
    return True  # Вернуть False для прерывания выполнения
```

### Функция finalize

Вызывается после выполнения всех шагов конфигурации:

```python
def finalize(device_id, device_manager, image_processor, logger, success):
    """
    Завершение после выполнения конфигурации.
    
    Args:
        device_id: Идентификатор устройства.
        device_manager: Экземпляр менеджера устройств.
        image_processor: Экземпляр обработчика изображений.
        logger: Логгер для записи событий.
        success: Успешно ли выполнение конфигурации.
    """
    logger.info(f"Завершение для устройства {device_id} (успех: {success})")
    
    # Очистка и завершающие действия
```

## Работа с изображениями

Для работы с изображениями используется модуль `image_processor`. Вот основные функции:

### Поиск шаблона на изображении

```python
def find_image_and_click(device_id, device_manager, image_processor, logger, template_name, threshold=0.7):
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
    
    # Поиск шаблона на скриншоте
    template_result = image_processor.find_template(
        screenshot, 
        template_name, 
        threshold=threshold
    )
    
    if template_result:
        # Получение координат центра шаблона
        x, y = image_processor.get_template_center(template_result)
        
        # Нажатие на найденные координаты
        return device_manager.input_tap(device_id, x, y, f"Нажатие на {template_name}")
    else:
        logger.warning(f"Шаблон {template_name} не найден на скриншоте")
        return False
```

### Ожидание появления изображения

```python
def wait_for_image(device_id, device_manager, image_processor, logger, template_name, timeout=30, threshold=0.7):
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
            template_name, 
            threshold=threshold
        )
        
        if template_result:
            logger.info(f"Шаблон {template_name} найден на скриншоте")
            return True
        
        logger.debug(f"Ожидание шаблона {template_name}... ({int(time.time() - start_time)}/{timeout}с)")
        time.sleep(1)
    
    logger.warning(f"Превышено время ожидания шаблона {template_name}")
    return False
```

## Передача параметров

Вы можете передавать дополнительные параметры в функции шагов через словарь шага:

```python
# Определение шага с параметрами
'steps': [
    {
        'name': 'login',
        'description': 'Вход в приложение',
        'action': 'perform_login',
        'username': 'test_user',
        'password': 'password123',
        'remember_me': True
    }
]

# Функция для шага с доступом к параметрам
def perform_login(device_id, device_manager, image_processor, logger, **kwargs):
    username = kwargs.get('username', 'default_user')
    password = kwargs.get('password', '')
    remember_me = kwargs.get('remember_me', False)
    
    logger.info(f"Выполнение входа для пользователя {username} (запомнить: {remember_me})")
    
    # Код для выполнения входа
    
    return True
```

## Цепочки конфигураций

Вы можете создавать цепочки конфигураций, указывая имя следующей конфигурации в параметре `next_config`:

```python
CONFIG = {
    'name': 'login_config',
    'description': 'Вход в приложение',
    # ...
    'next_config': 'main_actions_config',  # Имя следующей конфигурации
    # ...
}
```

После успешного выполнения `login_config` автоматически будет запущена конфигурация `main_actions_config`.

## Примеры конфигураций

### Пример 1: Вход в приложение

```python
CONFIG = {
    'name': 'login_config',
    'description': 'Вход в приложение',
    'version': '1.0.0',
    'author': 'Admin',
    'next_config': None,
    'settings': {
        'action_interval': 500,
        'max_action_attempts': 5,
        'image_match_threshold': 0.7,
        'wait_timeout': 30
    },
    'actions': [
        {
            'type': 'restart_app',
            'package': 'com.example.app',
            'description': 'Запуск приложения',
            'wait_after': 3000
        },
        {
            'type': 'click_image',
            'template': 'login_button.png',
            'description': 'Нажатие на кнопку входа',
            'threshold': 0.8,
            'wait_after': 2000
        },
        {
            'type': 'click_image',
            'template': 'username_field.png',
            'description': 'Нажатие на поле имени пользователя',
            'wait_after': 1000
        },
        {
            'type': 'input_text',
            'text': 'test_user',
            'description': 'Ввод имени пользователя',
            'wait_after': 1000
        },
        {
            'type': 'click_image',
            'template': 'password_field.png',
            'description': 'Нажатие на поле пароля',
            'wait_after': 1000
        },
        {
            'type': 'input_text',
            'text': 'password123',
            'description': 'Ввод пароля',
            'wait_after': 1000
        },
        {
            'type': 'click_image',
            'template': 'submit_button.png',
            'description': 'Нажатие на кнопку подтверждения',
            'wait_after': 5000
        }
    ],
    'steps': [
        {
            'name': 'restart_app',
            'description': 'Запуск приложения',
            'action': 'restart_app',
            'package': 'com.example.app'
        },
        {
            'name': 'login',
            'description': 'Вход в приложение',
            'action': 'perform_login',
            'username': 'test_user',
            'password': 'password123'
        }
    ],
    'enabled_steps': {
        'restart_app': True,
        'login': True
    }
}

def restart_app(device_id, device_manager, image_processor, logger, **kwargs):
    package = kwargs.get('package', 'com.example.app')
    return device_manager.restart_app(device_id, package, f"Перезапуск {package}")

def perform_login(device_id, device_manager, image_processor, logger, **kwargs):
    username = kwargs.get('username', 'test_user')
    password = kwargs.get('password', 'password123')
    
    logger.info(f"Выполнение входа с логином {username}")
    
    # Поиск и нажатие на кнопку входа
    login_button_found = False
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            login_button = image_processor.find_template(
                screenshot, 
                'login_button.png', 
                threshold=0.8
            )
            
            if login_button:
                login_button_found = True
                x, y = image_processor.get_template_center(login_button)
                device_manager.input_tap(device_id, x, y, "Нажатие на кнопку входа")
                time.sleep(2)
    
    # Остальной код для выполнения входа
    # ...
    
    return True
```

### Пример 2: Автоматические действия в приложении

```python
CONFIG = {
    'name': 'app_actions',
    'description': 'Автоматические действия в приложении',
    'version': '1.0.0',
    'author': 'Admin',
    'next_config': None,
    'settings': {
        'action_interval': 500,
        'max_action_attempts': 5,
        'image_match_threshold': 0.7,
        'wait_timeout': 30
    },
    'steps': [
        {
            'name': 'collect_rewards',
            'description': 'Сбор ежедневных наград',
            'action': 'collect_daily_rewards'
        },
        {
            'name': 'complete_tasks',
            'description': 'Выполнение ежедневных заданий',
            'action': 'complete_daily_tasks',
            'task_count': 3
        },
        {
            'name': 'logout',
            'description': 'Выход из приложения',
            'action': 'perform_logout'
        }
    ],
    'enabled_steps': {
        'collect_rewards': True,
        'complete_tasks': True,
        'logout': True
    }
}

def collect_daily_rewards(device_id, device_manager, image_processor, logger, **kwargs):
    logger.info("Сбор ежедневных наград")
    
    # Нажатие на кнопку наград
    rewards_found = False
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        screenshot = image_processor.load_image(screenshot_path)
        if screenshot is not None:
            rewards_button = image_processor.find_template(
                screenshot, 
                'rewards_button.png', 
                threshold=0.8
            )
            
            if rewards_button:
                rewards_found = True
                x, y = image_processor.get_template_center(rewards_button)
                device_manager.input_tap(device_id, x, y, "Нажатие на кнопку наград")
                time.sleep(2)
    
    if not rewards_found:
        logger.warning("Кнопка наград не найдена")
        return False
    
    # Код для сбора наград
    # ...
    
    return True

def complete_daily_tasks(device_id, device_manager, image_processor, logger, **kwargs):
    task_count = kwargs.get('task_count', 3)
    logger.info(f"Выполнение {task_count} ежедневных заданий")
    
    # Код для выполнения заданий
    # ...
    
    return True

def perform_logout(device_id, device_manager, image_processor, logger, **kwargs):
    logger.info("Выход из приложения")
    
    # Код для выхода из приложения
    # ...
    
    return True
```

## Советы и рекомендации

1. **Используйте описательные имена** для шаблонов изображений и функций.

2. **Добавляйте логирование** для облегчения отладки:
   ```python
   logger.info("Выполнение действия X")
   logger.debug(f"Значение переменной: {var}")
   logger.warning("Предупреждение: условие не выполнено")
   logger.error("Ошибка при выполнении действия")
   ```

3. **Обрабатывайте ошибки** и предусматривайте альтернативные пути:
   ```python
   try:
       # Основной код
   except Exception as e:
       logger.error(f"Произошла ошибка: {e}")
       # Альтернативный путь или восстановление
   ```

4. **Добавляйте таймауты и паузы** для стабильной работы.

5. **Разбивайте сложные действия** на простые шаги.

6. **Используйте высокий порог совпадения** для критических элементов интерфейса.

7. **Тестируйте конфигурации** на разных устройствах и разрешениях экрана.

8. **Обновляйте шаблоны изображений** при изменении интерфейса приложения.

9. **Используйте относительные координаты** вместо абсолютных, если это возможно.

10. **Сохраняйте скриншоты** для отладки:
    ```python
    timestamp = int(time.time())
    screenshot_path = device_manager.take_screenshot(device_id)
    if screenshot_path:
        new_path = f"debug/screenshot_{timestamp}.png"
        os.makedirs("debug", exist_ok=True)
        import shutil
        shutil.copy(screenshot_path, new_path)
    ```

---

Если у вас остались вопросы или вам нужна помощь с созданием конфигураций, обратитесь к документации или создайте Issue на GitHub.