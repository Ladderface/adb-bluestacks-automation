# Руководство по установке ADB Блюстакс Автоматизация

## Содержание
1. [Системные требования](#системные-требования)
2. [Подготовка](#подготовка)
3. [Установка](#установка)
4. [Настройка BlueStacks](#настройка-bluestacks)
5. [Запуск программы](#запуск-программы)
6. [Возможные проблемы](#возможные-проблемы)
7. [Дополнительная конфигурация](#дополнительная-конфигурация)

## Системные требования

Для работы программы ADB Блюстакс Автоматизация требуются:

- Windows 10 или Windows 11 (64-бит)
- Python 3.8 или выше
- BlueStacks 5 (последняя версия)
- Не менее 4 ГБ оперативной памяти
- Не менее 5 ГБ свободного места на диске
- Интернет-соединение для установки зависимостей

## Подготовка

### 1. Установка Python

Если у вас еще не установлен Python, выполните следующие шаги:

1. Скачайте последнюю версию Python с официального сайта: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Запустите установщик и **обязательно установите флажок "Add Python to PATH"**
3. Завершите установку, следуя инструкциям на экране

### 2. Установка Git (опционально)

Для работы с системой контроля версий Git:

1. Скачайте и установите Git с официального сайта: [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. При установке выберите опцию "Git from the command line and also from 3rd-party software"
3. Остальные настройки можно оставить по умолчанию

## Установка

### Способ 1: Клонирование репозитория Git (рекомендуется)

1. Откройте командную строку Windows (cmd) или PowerShell
2. Перейдите в директорию, где хотите разместить проект
3. Выполните команду:
   ```
   git clone https://github.com/yourusername/adb-bluestacks-automation.git
   ```
4. Перейдите в директорию проекта:
   ```
   cd adb-bluestacks-automation
   ```
5. Запустите установочный скрипт:
   ```
   install.bat
   ```

### Способ 2: Загрузка ZIP-архива

1. Скачайте ZIP-архив проекта с GitHub: [https://github.com/yourusername/adb-bluestacks-automation/archive/refs/heads/main.zip](https://github.com/yourusername/adb-bluestacks-automation/archive/refs/heads/main.zip)
2. Распакуйте архив в удобное место на вашем компьютере
3. Откройте командную строку Windows (cmd) или PowerShell
4. Перейдите в директорию проекта:
   ```
   cd путь\к\распакованному\архиву
   ```
5. Запустите установочный скрипт:
   ```
   install.bat
   ```

### Что делает установочный скрипт?

Скрипт `install.bat` выполняет следующие действия:

1. Создает виртуальное окружение Python
2. Устанавливает все необходимые зависимости из файла `requirements.txt`
3. Проверяет наличие ADB на компьютере, при необходимости загружает и устанавливает его
4. Создает необходимые директории для работы программы
5. Проверяет конфигурационные файлы

## Настройка BlueStacks

Для работы с программой BlueStacks необходимо настроить:

### 1. Включение ADB в BlueStacks

1. Запустите BlueStacks 5
2. Откройте настройки BlueStacks (иконка в правом верхнем углу)
3. Перейдите в раздел "Дополнительно"
4. Включите опцию "Отладка по Android" (Android Debug Bridge или ADB)
5. Запомните или запишите номер порта, который указан в настройках ADB (обычно 5555)

### 2. Создание списка устройств

1. В директории проекта перейдите в папку `configs`
2. Откройте файл `devices.txt` в любом текстовом редакторе
3. Добавьте устройства в формате `IP:порт:название`:
   ```
   127.0.0.1:5555:BlueStacks_1
   127.0.0.1:5556:BlueStacks_2
   ```
   
   Где:
   - `127.0.0.1` - локальный IP-адрес (localhost)
   - `5555` - порт ADB в BlueStacks
   - `BlueStacks_1` - название устройства (необязательно)

4. Сохраните файл

### 3. Подготовка шаблонов изображений

1. В директории проекта перейдите в папку `screenshots/templates`
2. Разместите в этой папке все шаблоны изображений, которые будут использоваться для распознавания элементов интерфейса
3. Убедитесь, что имена файлов соответствуют тем, которые указаны в конфигурациях

## Запуск программы

После установки и настройки вы можете запустить программу:

1. Откройте командную строку Windows (cmd) или PowerShell
2. Перейдите в директорию проекта
3. Запустите скрипт:
   ```
   run.bat
   ```

При первом запуске программа выполнит следующие действия:
- Проверит соединение с ADB-сервером и при необходимости запустит его
- Проверит подключение к устройствам из списка `devices.txt`
- Загрузит все доступные конфигурации
- Отобразит интерактивный режим командной строки для управления

### Основные команды

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

## Возможные проблемы

### Не удается подключиться к устройству

1. Убедитесь, что BlueStacks запущен
2. Проверьте, включена ли функция отладки по Android в настройках BlueStacks
3. Проверьте, правильно ли указан порт в файле `devices.txt`
4. Попробуйте вручную подключиться через ADB:
   ```
   adb connect 127.0.0.1:5555
   ```
5. Если подключение не удается, перезапустите BlueStacks и попробуйте снова

### Программа не находит шаблоны изображений

1. Убедитесь, что шаблоны изображений размещены в папке `screenshots/templates`
2. Проверьте, что имена файлов соответствуют тем, которые указаны в конфигурациях
3. Попробуйте увеличить или уменьшить порог совпадения в конфигурации (параметр `image_match_threshold`)
4. Создайте новые скриншоты элементов интерфейса и замените ими старые шаблоны

### Другие проблемы

Если вы столкнулись с другими проблемами:

1. Проверьте логи в папке `logs`
2. Перезапустите программу с помощью команды `restart`
3. Перезапустите BlueStacks
4. Перезагрузите компьютер

## Дополнительная конфигурация

### Настройка расписания автоматизации

По умолчанию программа запускает автоматизацию каждый час в 5, 25 и 45 минут. Вы можете изменить это расписание:

1. Откройте файл `config.yaml` в корневой директории проекта
2. Найдите секцию `scheduler`
3. Измените параметр `run_minutes`:
   ```yaml
   scheduler:
     enabled: true
     run_minutes: [5, 25, 45]  # Измените на нужные минуты
   ```

### Настройка интеграций

Программа поддерживает интеграцию с Telegram, Google Sheets и API для распознавания изображений. Для настройки:

1. Откройте файл `config.yaml` в корневой директории проекта
2. Найдите секцию `integrations`
3. Настройте нужные интеграции:

```yaml
integrations:
  # Интеграция с Telegram
  telegram:
    enabled: true
    token: "ваш_токен_бота"
    chat_ids: [12345678, 87654321]
    
  # Интеграция с Google Sheets
  google_sheets:
    enabled: true
    credentials_file: "credentials.json"
    spreadsheet_id: "идентификатор_таблицы"
    
  # Интеграция с API для распознавания изображений
  openai:
    enabled: true
    api_key: "ваш_api_key"
```

Для более подробной информации по настройке интеграций обратитесь к документации в папке `docs`.

---

Если у вас остались вопросы или возникли проблемы с установкой, обратитесь к документации или создайте Issue на GitHub.