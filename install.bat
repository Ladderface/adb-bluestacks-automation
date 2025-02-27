@echo off
echo ===================================
echo Установка ADB Блюстакс Автоматизация
echo ===================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не установлен!
    echo Пожалуйста, установите Python 3.8 или выше с официального сайта:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Проверка наличия pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Pip не установлен!
    echo Попытка установки pip...
    python -m ensurepip --default-pip
    if %errorlevel% neq 0 (
        echo Не удалось установить pip. Пожалуйста, установите его вручную.
        pause
        exit /b 1
    )
)

:: Создание виртуального окружения
echo Создание виртуального окружения...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось создать виртуальное окружение!
    pause
    exit /b 1
)

:: Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

:: Установка зависимостей
echo Установка необходимых пакетов...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости!
    pause
    exit /b 1
)

:: Проверка наличия ADB
where adb >nul 2>&1
if %errorlevel% neq 0 (
    echo ADB не найден в системе. Загрузка и установка ADB...
    
    :: Создание папки для ADB, если она не существует
    if not exist "tools" mkdir tools
    
    :: Загрузка платформы-инструментов Android SDK
    echo Загрузка Android Platform Tools...
    powershell -Command "& { Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'tools\platform-tools.zip' }"
    
    :: Распаковка ZIP-файла
    echo Распаковка...
    powershell -Command "& { Expand-Archive -Path 'tools\platform-tools.zip' -DestinationPath 'tools' -Force }"
    
    :: Копирование ADB в корневую папку проекта для удобства
    copy tools\platform-tools\adb.exe adb.exe >nul
    
    echo ADB установлен успешно!
) else (
    echo ADB уже установлен в системе.
)

:: Создание необходимых папок
echo Создание структуры проекта...
if not exist "configs" mkdir configs
if not exist "screenshots" mkdir screenshots
if not exist "screenshots\templates" mkdir screenshots\templates
if not exist "screenshots\output" mkdir screenshots\output
if not exist "logs" mkdir logs

echo.
echo ===================================
echo Установка завершена успешно!
echo ===================================
echo.
echo Для запуска программы используйте команду:
echo   run.bat
echo.
echo Документация доступна в папке docs/
echo.

pause