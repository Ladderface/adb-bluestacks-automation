@echo off
echo ===================================
echo Запуск ADB Блюстакс Автоматизация
echo ===================================
echo.

:: Активация виртуального окружения
call venv\Scripts\activate.bat

:: Запуск программы
python main.py %*

echo.
pause