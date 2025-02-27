#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль обработки изображений для ADB Блюстакс Автоматизация.
Обеспечивает обнаружение шаблонов на скриншотах и поиск областей интереса.
"""

import os
import cv2
import numpy as np
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union


class ImageProcessor:
    """
    Класс для обработки изображений, поиска шаблонов и областей интереса на скриншотах.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Инициализация обработчика изображений.
        
        Args:
            config: Конфигурация обработки изображений.
            logger: Логгер для записи событий.
        """
        self.config = config
        self.logger = logger
        
        # Каталог с шаблонами изображений
        self.templates_dir = config.get('directories', {}).get('templates', 'screenshots/templates')
        
        # Каталог для выходных изображений
        self.output_dir = config.get('directories', {}).get('output', 'screenshots/output')
        
        # Порог совпадения для поиска шаблонов
        self.threshold = config.get('execution', {}).get('image_match_threshold', 0.7)
        
        # Кэш загруженных шаблонов
        self.template_cache = {}
        
        # Создание необходимых директорий
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Обновление конфигурации обработчика изображений.
        
        Args:
            config: Новая конфигурация.
        """
        self.config = config
        self.templates_dir = config.get('directories', {}).get('templates', self.templates_dir)
        self.output_dir = config.get('directories', {}).get('output', self.output_dir)
        self.threshold = config.get('execution', {}).get('image_match_threshold', self.threshold)

    def load_template(self, template_name: str) -> Optional[np.ndarray]:
        """
        Загрузка шаблона изображения из файла.
        
        Args:
            template_name: Имя шаблона (с расширением или без).
            
        Returns:
            Optional[np.ndarray]: Загруженный шаблон или None в случае ошибки.
        """
        try:
            # Проверка, загружен ли шаблон уже в кэш
            if template_name in self.template_cache:
                return self.template_cache[template_name]
            
            # Добавление расширения, если его нет
            if not template_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                template_path = os.path.join(self.templates_dir, f"{template_name}.png")
                if not os.path.exists(template_path):
                    template_path = os.path.join(self.templates_dir, f"{template_name}.jpg")
                    if not os.path.exists(template_path):
                        self.logger.error(f"Шаблон не найден: {template_name}")
                        return None
            else:
                template_path = os.path.join(self.templates_dir, template_name)
                if not os.path.exists(template_path):
                    self.logger.error(f"Шаблон не найден: {template_name}")
                    return None
            
            # Загрузка шаблона
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            
            if template is None:
                self.logger.error(f"Не удалось загрузить шаблон: {template_path}")
                return None
            
            # Сохранение в кэш
            self.template_cache[template_name] = template
            
            self.logger.debug(f"Шаблон загружен: {template_name}, размер: {template.shape}")
            return template
            
        except Exception as e:
            self.logger.exception(f"Ошибка при загрузке шаблона {template_name}: {e}")
            return None

    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Загрузка изображения из файла.
        
        Args:
            image_path: Путь к изображению.
            
        Returns:
            Optional[np.ndarray]: Загруженное изображение или None в случае ошибки.
        """
        try:
            # Проверка существования файла
            if not os.path.exists(image_path):
                self.logger.error(f"Изображение не найдено: {image_path}")
                return None
            
            # Загрузка изображения
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            
            if image is None:
                self.logger.error(f"Не удалось загрузить изображение: {image_path}")
                return None
            
            return image
            
        except Exception as e:
            self.logger.exception(f"Ошибка при загрузке изображения {image_path}: {e}")
            return None

    def save_image(
        self, 
        image: np.ndarray, 
        filename: str, 
        directory: Optional[str] = None
    ) -> Optional[str]:
        """
        Сохранение изображения в файл.
        
        Args:
            image: Изображение для сохранения.
            filename: Имя файла.
            directory: Директория для сохранения (по умолчанию output_dir).
            
        Returns:
            Optional[str]: Путь к сохраненному файлу или None в случае ошибки.
        """
        try:
            # Определение директории для сохранения
            save_dir = directory or self.output_dir
            os.makedirs(save_dir, exist_ok=True)
            
            # Добавление расширения, если его нет
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filename = f"{filename}.png"
            
            # Формирование полного пути
            save_path = os.path.join(save_dir, filename)
            
            # Сохранение изображения
            cv2.imwrite(save_path, image)
            
            self.logger.debug(f"Изображение сохранено: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.exception(f"Ошибка при сохранении изображения {filename}: {e}")
            return None

    def find_template(
        self, 
        image: np.ndarray, 
        template_name: str, 
        threshold: Optional[float] = None,
        debug: bool = False
    ) -> Optional[Tuple[int, int, int, int, float]]:
        """
        Поиск шаблона на изображении.
        
        Args:
            image: Изображение для поиска.
            template_name: Имя шаблона.
            threshold: Порог совпадения (по умолчанию из конфигурации).
            debug: Сохранять ли отладочное изображение с результатом поиска.
            
        Returns:
            Optional[Tuple[int, int, int, int, float]]: Координаты найденного шаблона (x, y, w, h) и коэффициент совпадения 
            или None, если шаблон не найден.
        """
        try:
            # Загрузка шаблона
            template = self.load_template(template_name)
            if template is None:
                return None
            
            # Использование порога из параметра или конфигурации
            match_threshold = threshold if threshold is not None else self.threshold
            
            # Применение алгоритма сопоставления шаблонов
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            
            # Поиск максимального совпадения
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Проверка порога совпадения
            if max_val < match_threshold:
                self.logger.debug(f"Шаблон {template_name} не найден. "
                                f"Максимальное совпадение: {max_val:.2f}, порог: {match_threshold:.2f}")
                return None
            
            # Определение координат и размеров найденного шаблона
            x, y = max_loc
            w, h = template.shape[1], template.shape[0]
            
            self.logger.debug(f"Шаблон {template_name} найден в координатах ({x}, {y}) "
                            f"с совпадением {max_val:.2f}")
            
            # Сохранение отладочного изображения
            if debug:
                debug_image = image.copy()
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                timestamp = int(time.time())
                self.save_image(debug_image, f"debug_match_{template_name}_{timestamp}.png")
            
            return (x, y, w, h, max_val)
            
        except Exception as e:
            self.logger.exception(f"Ошибка при поиске шаблона {template_name}: {e}")
            return None

    def find_all_templates(
        self, 
        image: np.ndarray, 
        template_name: str, 
        threshold: Optional[float] = None,
        max_results: int = 10,
        debug: bool = False
    ) -> List[Tuple[int, int, int, int, float]]:
        """
        Поиск всех вхождений шаблона на изображении.
        
        Args:
            image: Изображение для поиска.
            template_name: Имя шаблона.
            threshold: Порог совпадения (по умолчанию из конфигурации).
            max_results: Максимальное количество результатов.
            debug: Сохранять ли отладочное изображение с результатами поиска.
            
        Returns:
            List[Tuple[int, int, int, int, float]]: Список найденных шаблонов (x, y, w, h, score).
        """
        try:
            # Загрузка шаблона
            template = self.load_template(template_name)
            if template is None:
                return []
            
            # Использование порога из параметра или конфигурации
            match_threshold = threshold if threshold is not None else self.threshold
            
            # Применение алгоритма сопоставления шаблонов
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            
            # Создание маски для исключения уже найденных совпадений
            w, h = template.shape[1], template.shape[0]
            
            # Список для хранения найденных шаблонов
            found_templates = []
            
            # Поиск всех вхождений шаблона
            count = 0
            while count < max_results:
                # Поиск максимального совпадения
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # Проверка порога совпадения
                if max_val < match_threshold:
                    break
                
                x, y = max_loc
                found_templates.append((x, y, w, h, max_val))
                count += 1
                
                # Исключение найденного региона из дальнейшего поиска
                result[y-h//2:y+h//2+h, x-w//2:x+w//2+w] = 0
            
            # Сохранение отладочного изображения
            if debug and found_templates:
                debug_image = image.copy()
                for x, y, w, h, score in found_templates:
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(debug_image, f"{score:.2f}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                timestamp = int(time.time())
                self.save_image(debug_image, f"debug_match_all_{template_name}_{timestamp}.png")
            
            return found_templates
            
        except Exception as e:
            self.logger.exception(f"Ошибка при поиске всех вхождений шаблона {template_name}: {e}")
            return []

    def get_template_center(
        self, 
        template_result: Tuple[int, int, int, int, float]
    ) -> Tuple[int, int]:
        """
        Получение координат центра найденного шаблона.
        
        Args:
            template_result: Результат поиска шаблона (x, y, w, h, score).
            
        Returns:
            Tuple[int, int]: Координаты центра шаблона (x, y).
        """
        x, y, w, h, _ = template_result
        return (x + w // 2, y + h // 2)

    def get_roi(
        self, 
        image: np.ndarray, 
        x: int, 
        y: int, 
        width: int, 
        height: int
    ) -> Optional[np.ndarray]:
        """
        Получение области интереса (ROI) из изображения.
        
        Args:
            image: Исходное изображение.
            x: Координата X левого верхнего угла области.
            y: Координата Y левого верхнего угла области.
            width: Ширина области.
            height: Высота области.
            
        Returns:
            Optional[np.ndarray]: Вырезанная область или None в случае ошибки.
        """
        try:
            # Проверка границ изображения
            img_height, img_width = image.shape[:2]
            
            # Корректировка координат, если они выходят за границы изображения
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            width = min(width, img_width - x)
            height = min(height, img_height - y)
            
            # Вырезание области
            roi = image[y:y+height, x:x+width]
            
            return roi
            
        except Exception as e:
            self.logger.exception(f"Ошибка при получении области интереса: {e}")
            return None

    def compare_images(
        self, 
        image1: np.ndarray, 
        image2: np.ndarray
    ) -> float:
        """
        Сравнение двух изображений.
        
        Args:
            image1: Первое изображение.
            image2: Второе изображение.
            
        Returns:
            float: Коэффициент сходства изображений (от 0 до 1).
        """
        try:
            # Проверка наличия изображений
            if image1 is None or image2 is None:
                return 0.0
            
            # Приведение изображений к одному размеру
            if image1.shape != image2.shape:
                image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
            
            # Вычисление среднеквадратической ошибки
            err = np.sum((image1.astype("float") - image2.astype("float")) ** 2)
            err /= float(image1.shape[0] * image1.shape[1] * image1.shape[2])
            
            # Преобразование ошибки в коэффициент сходства
            similarity = 1 - (err / 195075.0)  # Максимальная возможная ошибка для 8-битных изображений
            similarity = max(0, min(similarity, 1))  # Ограничение диапазона от 0 до 1
            
            return similarity
            
        except Exception as e:
            self.logger.exception(f"Ошибка при сравнении изображений: {e}")
            return 0.0

    def detect_text_area(
        self, 
        image: np.ndarray, 
        debug: bool = False
    ) -> List[Tuple[int, int, int, int]]:
        """
        Обнаружение областей с текстом на изображении.
        
        Args:
            image: Изображение для анализа.
            debug: Сохранять ли отладочное изображение с результатами обнаружения.
            
        Returns:
            List[Tuple[int, int, int, int]]: Список координат областей с текстом (x, y, w, h).
        """
        try:
            # Создание копии изображения для обработки
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Применение бинаризации для выделения текста
            _, thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Применение морфологических операций для улучшения обнаружения
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # Поиск контуров
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Фильтрация контуров
            text_areas = []
            for contour in contours:
                # Получение ограничивающего прямоугольника
                x, y, w, h = cv2.boundingRect(contour)
                
                # Фильтрация контуров по размеру (можно настроить под конкретные задачи)
                if w > 20 and h > 10 and w < image.shape[1] * 0.8 and h < image.shape[0] * 0.8:
                    text_areas.append((x, y, w, h))
            
            # Сохранение отладочного изображения
            if debug and text_areas:
                debug_image = image.copy()
                for x, y, w, h in text_areas:
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                timestamp = int(time.time())
                self.save_image(debug_image, f"debug_text_areas_{timestamp}.png")
            
            return text_areas
            
        except Exception as e:
            self.logger.exception(f"Ошибка при обнаружении областей с текстом: {e}")
            return []

    def detect_color_area(
        self, 
        image: np.ndarray, 
        lower_color: Tuple[int, int, int], 
        upper_color: Tuple[int, int, int],
        min_area: int = 100,
        debug: bool = False
    ) -> List[Tuple[int, int, int, int]]:
        """
        Обнаружение областей определенного цвета на изображении.
        
        Args:
            image: Изображение для анализа.
            lower_color: Нижняя граница цвета в формате BGR.
            upper_color: Верхняя граница цвета в формате BGR.
            min_area: Минимальная площадь области для фильтрации.
            debug: Сохранять ли отладочное изображение с результатами обнаружения.
            
        Returns:
            List[Tuple[int, int, int, int]]: Список координат областей с указанным цветом (x, y, w, h).
        """
        try:
            # Перевод изображения в формат HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Преобразование границ цвета из BGR в HSV
            lower_bgr = np.array(lower_color, dtype=np.uint8)
            upper_bgr = np.array(upper_color, dtype=np.uint8)
            lower_hsv = cv2.cvtColor(np.array([[lower_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
            upper_hsv = cv2.cvtColor(np.array([[upper_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
            
            # Создание маски для выделения пикселей указанного цвета
            mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
            
            # Применение морфологических операций для улучшения маски
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # Поиск контуров
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Фильтрация контуров по площади
            color_areas = []
            for contour in contours:
                # Вычисление площади контура
                area = cv2.contourArea(contour)
                
                if area >= min_area:
                    # Получение ограничивающего прямоугольника
                    x, y, w, h = cv2.boundingRect(contour)
                    color_areas.append((x, y, w, h))
            
            # Сохранение отладочного изображения
            if debug and color_areas:
                debug_image = image.copy()
                for x, y, w, h in color_areas:
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 255), 2)
                timestamp = int(time.time())
                self.save_image(debug_image, f"debug_color_areas_{timestamp}.png")
            
            return color_areas
            
        except Exception as e:
            self.logger.exception(f"Ошибка при обнаружении областей цвета: {e}")
            return []

    def detect_features(
        self, 
        image: np.ndarray, 
        debug: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Обнаружение характерных точек на изображении.
        
        Args:
            image: Изображение для анализа.
            debug: Сохранять ли отладочное изображение с результатами обнаружения.
            
        Returns:
            List[Tuple[int, int]]: Список координат характерных точек (x, y).
        """
        try:
            # Создание детектора характерных точек
            detector = cv2.SIFT_create()
            
            # Обнаружение характерных точек
            keypoints = detector.detect(image, None)
            
            # Преобразование keypoints в список координат
            features = [(int(kp.pt[0]), int(kp.pt[1])) for kp in keypoints]
            
            # Сохранение отладочного изображения
            if debug and features:
                debug_image = image.copy()
                for kp in keypoints:
                    x, y = int(kp.pt[0]), int(kp.pt[1])
                    cv2.circle(debug_image, (x, y), 3, (0, 255, 0), -1)
                timestamp = int(time.time())
                self.save_image(debug_image, f"debug_features_{timestamp}.png")
            
            return features
            
        except Exception as e:
            self.logger.exception(f"Ошибка при обнаружении характерных точек: {e}")
            return []

    def find_template_with_mask(
        self, 
        image: np.ndarray, 
        template_name: str, 
        mask_name: str,
        threshold: Optional[float] = None,
        debug: bool = False
    ) -> Optional[Tuple[int, int, int, int, float]]:
        """
        Поиск шаблона на изображении с использованием маски.
        
        Args:
            image: Изображение для поиска.
            template_name: Имя шаблона.
            mask_name: Имя файла маски.
            threshold: Порог совпадения (по умолчанию из конфигурации).
            debug: Сохранять ли отладочное изображение с результатом поиска.
            
        Returns:
            Optional[Tuple[int, int, int, int, float]]: Координаты найденного шаблона (x, y, w, h) и коэффициент совпадения 
            или None, если шаблон не найден.
        """
        try:
            # Загрузка шаблона
            template = self.load_template(template_name)
            if template is None:
                return None
            
            # Загрузка маски
            mask = self.load_template(mask_name)
            if mask is None:
                return None
            
            # Преобразование маски в одноканальное изображение
            if len(mask.shape) > 2:
                mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            
            # Использование порога из параметра или конфигурации
            match_threshold = threshold if threshold is not None else self.threshold
            
            # Применение алгоритма сопоставления шаблонов с маской
            result = cv2.matchTemplate(image, template, cv2.TM_CCORR_NORMED, mask=mask)
            
            # Поиск максимального совпадения
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Проверка порога совпадения
            if max_val < match_threshold:
                self.logger.debug(f"Шаблон {template_name} с маской {mask_name} не найден. "
                                f"Максимальное совпадение: {max_val:.2f}, порог: {match_threshold:.2f}")
                return None
            
            # Определение координат и размеров найденного шаблона
            x, y = max_loc
            w, h = template.shape[1], template.shape[0]
            
            self.logger.debug(f"Шаблон {template_name} с маской {mask_name} найден в координатах ({x}, {y}) "
                            f"с совпадением {max_val:.2f}")
            
            # Сохранение отладочного изображения
            if debug:
                debug_image = image.copy()
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                timestamp = int(time.time())
                self.save_image(debug_image, f"debug_match_mask_{template_name}_{timestamp}.png")
            
            return (x, y, w, h, max_val)
            
        except Exception as e:
            self.logger.exception(f"Ошибка при поиске шаблона {template_name} с маской {mask_name}: {e}")
            return None

    def crop_image(
        self, 
        image: np.ndarray, 
        x: int, 
        y: int, 
        width: int, 
        height: int
    ) -> Optional[np.ndarray]:
        """
        Обрезка изображения по указанным координатам.
        
        Args:
            image: Исходное изображение.
            x: Координата X левого верхнего угла области.
            y: Координата Y левого верхнего угла области.
            width: Ширина области.
            height: Высота области.
            
        Returns:
            Optional[np.ndarray]: Обрезанное изображение или None в случае ошибки.
        """
        return self.get_roi(image, x, y, width, height)

    def highlight_region(
        self, 
        image: np.ndarray, 
        x: int, 
        y: int, 
        width: int, 
        height: int, 
        color: Tuple[int, int, int] = (0, 255, 0), 
        thickness: int = 2
    ) -> np.ndarray:
        """
        Выделение области на изображении.
        
        Args:
            image: Исходное изображение.
            x: Координата X левого верхнего угла области.
            y: Координата Y левого верхнего угла области.
            width: Ширина области.
            height: Высота области.
            color: Цвет выделения в формате BGR.
            thickness: Толщина линии выделения.
            
        Returns:
            np.ndarray: Изображение с выделенной областью.
        """
        try:
            # Создание копии изображения
            result = image.copy()
            
            # Рисование прямоугольника
            cv2.rectangle(result, (x, y), (x + width, y + height), color, thickness)
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Ошибка при выделении области на изображении: {e}")
            return image

    def add_text(
        self, 
        image: np.ndarray, 
        text: str, 
        x: int, 
        y: int, 
        font_scale: float = 1.0, 
        color: Tuple[int, int, int] = (0, 255, 0), 
        thickness: int = 2
    ) -> np.ndarray:
        """
        Добавление текста на изображение.
        
        Args:
            image: Исходное изображение.
            text: Текст для добавления.
            x: Координата X левого нижнего угла текста.
            y: Координата Y левого нижнего угла текста.
            font_scale: Масштаб шрифта.
            color: Цвет текста в формате BGR.
            thickness: Толщина линий текста.
            
        Returns:
            np.ndarray: Изображение с добавленным текстом.
        """
        try:
            # Создание копии изображения
            result = image.copy()
            
            # Добавление текста
            cv2.putText(result, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Ошибка при добавлении текста на изображение: {e}")
            return image

    def resize_image(
        self, 
        image: np.ndarray, 
        width: Optional[int] = None, 
        height: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        Изменение размера изображения.
        
        Args:
            image: Исходное изображение.
            width: Новая ширина (если None, сохраняется соотношение сторон).
            height: Новая высота (если None, сохраняется соотношение сторон).
            
        Returns:
            Optional[np.ndarray]: Изображение с измененным размером или None в случае ошибки.
        """
        try:
            # Получение текущих размеров
            h, w = image.shape[:2]
            
            # Вычисление новых размеров с сохранением соотношения сторон
            if width is None and height is None:
                return image
            
            if width is None:
                ratio = height / h
                new_width = int(w * ratio)
                new_height = height
            elif height is None:
                ratio = width / w
                new_width = width
                new_height = int(h * ratio)
            else:
                new_width = width
                new_height = height
            
            # Изменение размера
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return resized
            
        except Exception as e:
            self.logger.exception(f"Ошибка при изменении размера изображения: {e}")
            return None

    def convert_to_grayscale(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Преобразование изображения в оттенки серого.
        
        Args:
            image: Исходное изображение.
            
        Returns:
            Optional[np.ndarray]: Изображение в оттенках серого или None в случае ошибки.
        """
        try:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            self.logger.exception(f"Ошибка при преобразовании изображения в оттенки серого: {e}")
            return None

    def apply_threshold(
        self, 
        image: np.ndarray, 
        threshold: int = 127, 
        max_value: int = 255, 
        threshold_type: int = cv2.THRESH_BINARY
    ) -> Optional[np.ndarray]:
        """
        Применение порогового преобразования к изображению.
        
        Args:
            image: Исходное изображение.
            threshold: Значение порога.
            max_value: Максимальное значение для бинаризации.
            threshold_type: Тип порогового преобразования.
            
        Returns:
            Optional[np.ndarray]: Изображение после порогового преобразования или None в случае ошибки.
        """
        try:
            # Преобразование в оттенки серого, если изображение цветное
            if len(image.shape) > 2:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Применение порогового преобразования
            _, thresholded = cv2.threshold(gray, threshold, max_value, threshold_type)
            
            return thresholded
            
        except Exception as e:
            self.logger.exception(f"Ошибка при применении порогового преобразования: {e}")
            return None

    def combine_images(
        self, 
        images: List[np.ndarray], 
        horizontal: bool = True
    ) -> Optional[np.ndarray]:
        """
        Объединение нескольких изображений в одно.
        
        Args:
            images: Список изображений для объединения.
            horizontal: Объединять по горизонтали (True) или по вертикали (False).
            
        Returns:
            Optional[np.ndarray]: Объединенное изображение или None в случае ошибки.
        """
        try:
            if not images:
                return None
            
            if len(images) == 1:
                return images[0]
            
            # Приведение всех изображений к одинаковой высоте или ширине
            if horizontal:
                # Определение максимальной высоты
                max_height = max(img.shape[0] for img in images)
                
                # Изменение размеров изображений
                resized_images = []
                for img in images:
                    if img.shape[0] != max_height:
                        resized = cv2.resize(img, (int(img.shape[1] * max_height / img.shape[0]), max_height))
                        resized_images.append(resized)
                    else:
                        resized_images.append(img)
                
                # Объединение по горизонтали
                return cv2.hconcat(resized_images)
                
            else:
                # Определение максимальной ширины
                max_width = max(img.shape[1] for img in images)
                
                # Изменение размеров изображений
                resized_images = []
                for img in images:
                    if img.shape[1] != max_width:
                        resized = cv2.resize(img, (max_width, int(img.shape[0] * max_width / img.shape[1])))
                        resized_images.append(resized)
                    else:
                        resized_images.append(img)
                
                # Объединение по вертикали
                return cv2.vconcat(resized_images)
                
        except Exception as e:
            self.logger.exception(f"Ошибка при объединении изображений: {e}")
            return None