#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль консольного интерфейса для ADB Блюстакс Автоматизация.
Обеспечивает отображение информации в консоли и интерактивный CLI.
"""

import os
import sys
import asyncio
import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from concurrent.futures import ThreadPoolExecutor


class ConsoleUI:
    """
    Класс для работы с консольным интерфейсом приложения.
    Обеспечивает форматированный вывод информации и интерактивный CLI.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Инициализация консольного интерфейса.
        
        Args:
            config: Конфигурация пользовательского интерфейса.
            logger: Логгер для записи событий.
        """
        self.config = config
        self.logger = logger
        self.console = Console()
        self.style = config.get('style', 'rich')
        self.show_progress = config.get('show_progress', True)
        self.update_interval = config.get('update_interval', 100) / 1000  # Конвертация в секунды
        self.max_lines = config.get('max_lines', 50)
        self.show_system_messages = config.get('show_system_messages', True)
        
        # Словарь прогресс-баров для устройств
        self.device_progress = {}
        
        # Создание блокировки для потокобезопасного вывода
        self.print_lock = threading.Lock()
        
        # Пул потоков для асинхронных операций UI
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # Состояние приложения
        self.running = False
        self.cli_running = False
        
        # Очистка консоли при запуске
        self._clear_console()

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Обновление конфигурации пользовательского интерфейса.
        
        Args:
            config: Новая конфигурация.
        """
        self.config = config
        self.style = config.get('style', self.style)
        self.show_progress = config.get('show_progress', self.show_progress)
        self.update_interval = config.get('update_interval', self.update_interval * 1000) / 1000
        self.max_lines = config.get('max_lines', self.max_lines)
        self.show_system_messages = config.get('show_system_messages', self.show_system_messages)

    def _clear_console(self) -> None:
        """Очистка консоли с учетом операционной системы."""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Linux/Mac
            os.system('clear')

    def print_header(self, text: str) -> None:
        """
        Вывод заголовка в консоль.
        
        Args:
            text: Текст заголовка.
        """
        with self.print_lock:
            if self.style == 'rich':
                header = Text(text, style="bold blue")
                self.console.print(Panel(header, border_style="blue"))
            else:
                print("\n" + "=" * 50)
                print(f"{text:^50}")
                print("=" * 50 + "\n")

    def print_info(self, message: str) -> None:
        """
        Вывод информационного сообщения.
        
        Args:
            message: Текст сообщения.
        """
        with self.print_lock:
            if self.style == 'rich':
                self.console.print(f"[bold cyan]INFO:[/bold cyan] {message}")
            else:
                print(f"[INFO] {message}")
        self.logger.info(message)

    def print_success(self, message: str) -> None:
        """
        Вывод сообщения об успешном выполнении.
        
        Args:
            message: Текст сообщения.
        """
        with self.print_lock:
            if self.style == 'rich':
                self.console.print(f"[bold green]УСПЕХ:[/bold green] {message}")
            else:
                print(f"[УСПЕХ] {message}")
        self.logger.info(message)

    def print_warning(self, message: str) -> None:
        """
        Вывод предупреждения.
        
        Args:
            message: Текст предупреждения.
        """
        with self.print_lock:
            if self.style == 'rich':
                self.console.print(f"[bold yellow]ПРЕДУПРЕЖДЕНИЕ:[/bold yellow] {message}")
            else:
                print(f"[ПРЕДУПРЕЖДЕНИЕ] {message}")
        self.logger.warning(message)

    def print_error(self, message: str) -> None:
        """
        Вывод сообщения об ошибке.
        
        Args:
            message: Текст сообщения об ошибке.
        """
        with self.print_lock:
            if self.style == 'rich':
                self.console.print(f"[bold red]ОШИБКА:[/bold red] {message}")
            else:
                print(f"[ОШИБКА] {message}")
        self.logger.error(message)

    def print_device_message(self, device_id: str, message: str, level: str = 'INFO') -> None:
        """
        Вывод сообщения для конкретного устройства.
        
        Args:
            device_id: Идентификатор устройства.
            message: Текст сообщения.
            level: Уровень сообщения (INFO, WARNING, ERROR).
        """
        # Определение цвета для уровня
        if level == 'ERROR':
            color = 'red'
        elif level == 'WARNING':
            color = 'yellow'
        else:
            color = 'green'
        
        with self.print_lock:
            if self.style == 'rich':
                self.console.print(f"[cyan]{device_id}[/cyan] → [bold {color}]{message}[/bold {color}]")
            else:
                print(f"[{device_id}] {message}")
        
        # Логирование с соответствующим уровнем
        if level == 'ERROR':
            self.logger.error(f"[{device_id}] {message}")
        elif level == 'WARNING':
            self.logger.warning(f"[{device_id}] {message}")
        else:
            self.logger.info(f"[{device_id}] {message}")

    def create_progress(self, device_id: str, description: str, total: int = 100) -> None:
        """
        Создание прогресс-бара для устройства.
        
        Args:
            device_id: Идентификатор устройства.
            description: Описание процесса.
            total: Общее количество шагов.
        """
        if not self.show_progress:
            return
        
        with self.print_lock:
            if device_id in self.device_progress:
                # Если прогресс-бар уже существует, обновим его
                self.device_progress[device_id]['total'] = total
                self.device_progress[device_id]['current'] = 0
                self.device_progress[device_id]['description'] = description
            else:
                # Создаем новый прогресс-бар
                self.device_progress[device_id] = {
                    'total': total,
                    'current': 0,
                    'description': description,
                    'start_time': time.time()
                }

    def update_progress(self, device_id: str, advance: int = 1, description: Optional[str] = None) -> None:
        """
        Обновление прогресс-бара для устройства.
        
        Args:
            device_id: Идентификатор устройства.
            advance: Количество шагов для продвижения.
            description: Новое описание (опционально).
        """
        if not self.show_progress or device_id not in self.device_progress:
            return
        
        with self.print_lock:
            progress = self.device_progress[device_id]
            progress['current'] += advance
            
            if description:
                progress['description'] = description
            
            # Ограничение до максимального значения
            if progress['current'] > progress['total']:
                progress['current'] = progress['total']
            
            # Вычисление процента выполнения
            percent = int((progress['current'] / progress['total']) * 100)
            
            # Вычисление затраченного времени
            elapsed = time.time() - progress['start_time']
            
            # Отображение прогресса
            if self.style == 'rich':
                progress_bar = f"[{'=' * (percent // 5)}{' ' * (20 - percent // 5)}]"
                self.console.print(f"[cyan]{device_id}[/cyan] {progress_bar} {percent}% - {progress['description']}")
            else:
                print(f"[{device_id}] {percent}% - {progress['description']}")

    def complete_progress(self, device_id: str, success: bool = True) -> None:
        """
        Завершение прогресс-бара для устройства.
        
        Args:
            device_id: Идентификатор устройства.
            success: Успешно ли завершена операция.
        """
        if not self.show_progress or device_id not in self.device_progress:
            return
        
        with self.print_lock:
            progress = self.device_progress[device_id]
            progress['current'] = progress['total']
            
            # Вычисление затраченного времени
            elapsed = time.time() - progress['start_time']
            
            # Отображение финального прогресса
            status = "Завершено" if success else "Прервано"
            
            if self.style == 'rich':
                self.console.print(f"[cyan]{device_id}[/cyan] → [{'green' if success else 'red'}]{status}[/{'green' if success else 'red'}] "
                                 f"({elapsed:.1f}с) - {progress['description']}")
            else:
                print(f"[{device_id}] {status} ({elapsed:.1f}с) - {progress['description']}")
            
            # Удаление прогресс-бара
            del self.device_progress[device_id]

    def print_device_table(self, devices: Dict[str, Dict[str, Any]]) -> None:
        """
        Вывод таблицы устройств.
        
        Args:
            devices: Словарь с информацией об устройствах.
        """
        with self.print_lock:
            if self.style == 'rich':
                table = Table(title="Список устройств")
                
                table.add_column("ID", style="cyan")
                table.add_column("Название", style="green")
                table.add_column("Статус", style="magenta")
                table.add_column("Действие", style="yellow")
                
                for device_id, device_info in devices.items():
                    status_color = "green" if device_info.get('connected', False) else "red"
                    status = f"[{status_color}]{device_info.get('status', 'Отключено')}[/{status_color}]"
                    
                    table.add_row(
                        device_id,
                        device_info.get('name', '-'),
                        status,
                        device_info.get('current_action', '-')
                    )
                
                self.console.print(table)
            else:
                print("\nСписок устройств:")
                print("-" * 80)
                print(f"{'ID':<20} {'Название':<20} {'Статус':<15} {'Действие':<25}")
                print("-" * 80)
                
                for device_id, device_info in devices.items():
                    print(f"{device_id:<20} {device_info.get('name', '-'):<20} "
                          f"{device_info.get('status', 'Отключено'):<15} "
                          f"{device_info.get('current_action', '-'):<25}")
                
                print("-" * 80 + "\n")

    async def start_cli(self, app) -> None:
        """
        Запуск интерактивного режима командной строки.
        
        Args:
            app: Экземпляр основного приложения.
        """
        self.cli_running = True
        self.print_info("Запуск интерактивного режима. Введите 'help' для списка команд.")
        
        # Справка по командам
        help_text = """
        Доступные команды:
        - help             : Показать эту справку
        - status           : Показать статус устройств
        - start [config]   : Запустить автоматизацию (опционально с указанием конфига)
        - stop             : Остановить текущую автоматизацию
        - pause            : Приостановить автоматизацию
        - resume           : Возобновить автоматизацию
        - reload           : Перезагрузить конфигурацию
        - connect <device> : Подключиться к устройству
        - disconnect <device> : Отключиться от устройства
        - screenshot <device> : Сделать скриншот устройства
        - clear            : Очистить консоль
        - exit             : Выйти из программы
        """
        
        while self.cli_running and app.running:
            try:
                # Использование thread_pool для неблокирующего ввода
                loop = asyncio.get_event_loop()
                command = await loop.run_in_executor(
                    self.thread_pool, 
                    lambda: Prompt.ask("[bold blue]Команда[/bold blue]") if self.style == 'rich' else input("Команда> ")
                )
                
                command = command.strip().lower()
                parts = command.split()
                
                if not parts:
                    continue
                
                if parts[0] == 'help':
                    self.console.print(Panel(help_text, title="Справка по командам", border_style="blue"))
                
                elif parts[0] == 'status':
                    if app.device_manager:
                        await app.device_manager.update_device_statuses()
                        self.print_device_table(app.device_manager.devices)
                    else:
                        self.print_error("Менеджер устройств не инициализирован")
                
                elif parts[0] == 'start':
                    config_name = parts[1] if len(parts) > 1 else None
                    if config_name:
                        self.print_info(f"Запуск конфига {config_name}...")
                        await app.scheduler.run_specific_config(config_name)
                    else:
                        self.print_info("Запуск автоматизации...")
                        await app.scheduler.run_automation()
                
                elif parts[0] == 'stop':
                    self.print_info("Остановка автоматизации...")
                    await app.scheduler.stop_automation()
                
                elif parts[0] == 'pause':
                    self.print_info("Приостановка автоматизации...")
                    await app.scheduler.pause_automation()
                
                elif parts[0] == 'resume':
                    self.print_info("Возобновление автоматизации...")
                    await app.scheduler.resume_automation()
                
                elif parts[0] == 'reload':
                    await app.reload_config()
                
                elif parts[0] == 'connect' and len(parts) > 1:
                    device_id = parts[1]
                    self.print_info(f"Подключение к устройству {device_id}...")
                    await app.device_manager.connect_device(device_id)
                
                elif parts[0] == 'disconnect' and len(parts) > 1:
                    device_id = parts[1]
                    self.print_info(f"Отключение от устройства {device_id}...")
                    await app.device_manager.disconnect_device(device_id)
                
                elif parts[0] == 'screenshot' and len(parts) > 1:
                    device_id = parts[1]
                    self.print_info(f"Создание скриншота устройства {device_id}...")
                    if app.device_manager:
                        await app.device_manager.take_screenshot(device_id)
                    else:
                        self.print_error("Менеджер устройств не инициализирован")
                
                elif parts[0] == 'clear':
                    self._clear_console()
                
                elif parts[0] == 'exit':
                    self.print_info("Завершение работы...")
                    self.cli_running = False
                    app.running = False
                    break
                
                else:
                    self.print_warning(f"Неизвестная команда: {command}")
                    self.print_info("Введите 'help' для списка доступных команд")
                
            except KeyboardInterrupt:
                self.print_info("Получен сигнал прерывания (Ctrl+C)")
                self.cli_running = False
                app.running = False
                break
            
            except Exception as e:
                self.print_error(f"Ошибка при обработке команды: {e}")
        
        self.cli_running = False