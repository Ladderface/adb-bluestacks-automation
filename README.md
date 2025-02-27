# ADB Блюстакс Автоматизация

Многопоточный и асинхронный инструмент для автоматизации работы с Android-эмуляторами BlueStacks 5 через протокол ADB.

## Возможности

- Подключение к нескольким экземплярам BlueStacks одновременно
- Многопоточная и асинхронная обработка устройств
- Гибкая система конфигураций через Python
- Автоматизация действий на основе распознавания изображений
- Расписание автоматического запуска
- Интерактивный режим командной строки
- Подробное логирование для каждого устройства
- Возможность интеграции с Telegram, Google Sheets и другими сервисами

## Системные требования

- Windows 10 или Windows 11 (64-бит)
- Python 3.8 или выше
- BlueStacks 5 (последняя версия)

## Установка

### Через Git

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/adb-bluestacks-automation.git

# Переход в директорию проекта
cd adb-bluestacks-automation

# Запуск установочного скрипта
install.bat
```

### Через ZIP-архив

1. Скачайте ZIP-архив проекта
2. Распакуйте архив в удобное место
3. Откройте командную строку в директории проекта
4. Запустите `install.bat`

## Быстрый старт

1. Запустите BlueStacks 5
2. Включите отладку по Android в настройках BlueStacks (вкладка "Дополнительно")
3. Отредактируйте файл `configs/devices.txt` и добавьте туда свои устройства:
   ```
   127.0.0.1:5555:BlueStacks_1
   ```
4. Запустите программу:
   ```
   run.bat
   ```

## Основные команды

После запуска программы вы можете использовать следующие команды:

- `help` - Показать справку по командам
- `status` - Показать статус устройств
- `start [config]` - Запустить автоматизацию (опционально с указанием конфига)
- `stop` - Остановить текущую автоматизацию
- `pause` - Приостановить автоматизацию
- `resume` - Возобновить автоматизацию
- `reload` - Перезагрузить конфигурацию
- `connect <device>` - Подключиться к устройству
- `disconnect <device>` - Отключиться от устройства
- `screenshot <device>` - Сделать скриншот устройства
- `clear` - Очистить консоль
- `exit` - Выйти из программы

## Конфигурации

Конфигурационные файлы размещаются в директории `configs/` и представляют собой Python-модули, описывающие последовательность действий для автоматизации.

Базовая структура конфигурационного файла:

```python
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

def initialize(device_id, device_manager, image_processor, logger):
    # Код инициализации
    return True

def finalize(device_id, device_manager, image_processor, logger, success):
    # Код завершения
    pass

# Пользовательские функции для шагов
def step_function1(device_id, device_manager, image_processor, logger, **kwargs):
    # Код функции
    return True
```

Подробное руководство по созданию конфигураций доступно в директории `docs/`.

## Структура проекта

```
adb-bluestacks-automation/
├── configs/                  # Конфигурационные файлы
│   ├── devices.txt           # Список устройств
│   ├── default_config.py     # Базовая конфигурация
│   └── sample_config.py      # Пример конфигурации
├── docs/                     # Документация
│   ├── installation.md       # Руководство по установке
│   └── config_guide.md       # Руководство по созданию конфигураций
├── logs/                     # Логи
├── modules/                  # Модули программы
├── screenshots/              # Директория для работы с изображениями
│   ├── templates/            # Шаблоны изображений для поиска
│   └── output/               # Выходные изображения
├── .gitignore                # Игнорируемые Git файлы
├── config.yaml               # Основной конфигурационный файл
├── install.bat               # Скрипт установки
├── main.py                   # Основной файл программы
├── README.md                 # Файл с описанием проекта
├── requirements.txt          # Зависимости Python
└── run.bat                   # Скрипт запуска
```

## Автоматический запуск

По умолчанию программа запускает автоматизацию каждый час в 5, 25 и 45 минут. Вы можете изменить это расписание в файле `config.yaml`:

```yaml
scheduler:
  enabled: true
  run_minutes: [5, 25, 45]  # Минуты для запуска (каждый час)
```

## Интеграции

Программа поддерживает интеграцию с:

- **Telegram**: получение уведомлений и управление через бота
- **Google Sheets**: запись результатов в таблицы
- **OpenAI**: распознавание изображений и текста

Настройка интеграций производится в файле `config.yaml`.

## Документация

Подробная документация доступна в директории `docs/`:

- [Руководство по установке](docs/installation.md)
- [Руководство по созданию конфигураций](docs/config_guide.md)

## Лицензия

[MIT](LICENSE)

## Авторы

- Автор проекта

## Благодарности

- [adbutils](https://github.com/openatx/adbutils) - Библиотека для работы с ADB
- [OpenCV](https://opencv.org/) - Библиотека компьютерного зрения