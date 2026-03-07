"""
Основной класс FileParser для универсального парсинга.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime

from parser.base import BaseParser
from parser.utils import (
    detect_format,
    detect_encoding,
    filter_data,
    ParseStats,
)
from parser.formats import get_parser_by_format, get_all_parsers


class FileParser:
    """
    Универсальный парсер файлов.

    Автоматически определяет формат файла и использует соответствующий парсер.
    """

    def __init__(self, custom_parsers: Optional[Dict[str, Type[BaseParser]]] = None):
        """
        Инициализация парсера.

        Args:
            custom_parsers: Пользовательские парсеры.
        """
        self.parsers: Dict[str, Type[BaseParser]] = {}
        self._load_builtin_parsers()

        if custom_parsers:
            self.parsers.update(custom_parsers)

        self.last_stats: Optional[ParseStats] = None

    def _load_builtin_parsers(self):
        """Загрузка встроенных парсеров."""
        self.parsers = get_all_parsers()

    def register_parser(self, format_name: str, parser_class: Type[BaseParser]):
        """
        Регистрация парсера.

        Args:
            format_name: Название формата.
            parser_class: Класс парсера.
        """
        self.parsers[format_name] = parser_class

    def get_parser(self, format_name: str) -> BaseParser:
        """
        Получение парсера по формату.

        Args:
            format_name: Название формата.

        Returns:
            Экземпляр парсера.

        Raises:
            ValueError: Если парсер не найден.
        """
        if format_name not in self.parsers:
            available = ", ".join(self.parsers.keys())
            raise ValueError(
                f"Парсер для формата '{format_name}' не найден. "
                f"Доступные форматы: {available}"
            )
        return self.parsers[format_name]()

    def parse(
        self,
        file_path: str,
        encoding: Optional[str] = None,
        format_name: Optional[str] = None,
        filter_keys: Optional[List[str]] = None,
        regex: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str, bytes]:
        """
        Парсинг файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка файла.
            format_name: Формат файла (если не указан, определяется автоматически).
            filter_keys: Ключи для фильтрации.
            regex: Регулярное выражение для фильтрации.
            start_line: Начальная строка.
            end_line: Конечная строка.
            **kwargs: Дополнительные параметры.

        Returns:
            Распарсенные данные.
        """
        stats = ParseStats()
        stats.start(file_path)

        try:
            # Определение кодировки
            if encoding is None:
                encoding = detect_encoding(file_path)
            stats.encoding = encoding

            # Определение формата
            if format_name is None:
                format_name = detect_format(file_path)

            if format_name is None:
                raise ValueError(
                    f"Не удалось определить формат файла: {file_path}"
                )

            stats.format = format_name

            # Получение парсера
            parser = self.get_parser(format_name)

            # Парсинг
            data = parser.parse(file_path, encoding=encoding, **kwargs)

            # Фильтрация
            data = filter_data(
                data,
                filter_keys=filter_keys,
                regex=regex,
                start_line=start_line,
                end_line=end_line,
            )

            # Подсчет записей
            if isinstance(data, list):
                stats.records_count = len(data)
            elif isinstance(data, dict):
                stats.records_count = len(data)

            stats.end()
            self.last_stats = stats

            return data

        except Exception as e:
            stats.add_error(str(e))
            stats.end()
            self.last_stats = stats
            raise

    def parse_batch(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Пакетный парсинг файлов.

        Args:
            file_paths: Список путей к файлам.
            output_dir: Директория для сохранения результатов.
            **kwargs: Параметры для парсинга.

        Returns:
            Словарь с результатами парсинга.
        """
        results = {}

        for file_path in file_paths:
            try:
                data = self.parse(file_path, **kwargs)

                if output_dir:
                    path = Path(file_path)
                    output_path = Path(output_dir) / f"{path.stem}.json"
                    self.save_json(data, str(output_path))

                results[file_path] = {
                    "success": True,
                    "data": data,
                    "stats": self.last_stats.to_dict() if self.last_stats else None,
                }

            except Exception as e:
                results[file_path] = {
                    "success": False,
                    "error": str(e),
                }

        return results

    def save(
        self,
        data: Union[Dict, List, str, bytes],
        file_path: str,
        format_name: Optional[str] = None,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение данных в файл.

        Args:
            data: Данные для сохранения.
            file_path: Путь к файлу.
            format_name: Формат файла.
            encoding: Кодировка.
            **kwargs: Дополнительные параметры.
        """
        if format_name is None:
            format_name = detect_format(file_path)

        if format_name is None:
            # Определение по расширению
            ext = Path(file_path).suffix.lower()
            format_map = {
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".csv": "csv",
                ".xlsx": "xlsx",
                ".xml": "xml",
                ".html": "html",
                ".md": "markdown",
                ".txt": "text",
            }
            format_name = format_map.get(ext, "text")

        parser = self.get_parser(format_name)
        parser.save(data, file_path, encoding=encoding, **kwargs)

    def save_json(self, data: Any, file_path: str, indent: int = 2) -> None:
        """Сохранение в JSON."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def convert(
        self,
        input_file: str,
        output_format: str,
        output_file: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Конвертация файла.

        Args:
            input_file: Входной файл.
            output_format: Выходной формат.
            output_file: Выходной файл (если не указан, создается автоматически).
            **kwargs: Дополнительные параметры.

        Returns:
            Путь к выходному файлу.
        """
        # Парсинг входного файла
        data = self.parse(input_file, **kwargs)

        # Определение выходного файла
        if output_file is None:
            input_path = Path(input_file)
            ext_map = {
                "json": ".json",
                "yaml": ".yaml",
                "csv": ".csv",
                "xlsx": ".xlsx",
                "xml": ".xml",
                "html": ".html",
                "markdown": ".md",
                "text": ".txt",
            }
            ext = ext_map.get(output_format, ".txt")
            output_file = str(input_path.with_suffix(ext))

        # Сохранение
        self.save(data, output_file, format_name=output_format)

        return output_file

    def analyze(
        self,
        file_path: str,
        filter_pattern: Optional[str] = None,
        regex: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Анализ файла.

        Args:
            file_path: Путь к файлу.
            filter_pattern: Паттерн для фильтрации.
            regex: Регулярное выражение.
            start_line: Начальная строка.
            end_line: Конечная строка.
            **kwargs: Дополнительные параметры.

        Returns:
            Результаты анализа.
        """
        data = self.parse(
            file_path,
            regex=regex,
            start_line=start_line,
            end_line=end_line,
            **kwargs
        )

        analysis = {
            "file": file_path,
            "format": self.last_stats.format if self.last_stats else "unknown",
            "encoding": self.last_stats.encoding if self.last_stats else "unknown",
            "size": self.last_stats.file_size if self.last_stats else 0,
            "records": self.last_stats.records_count if self.last_stats else 0,
            "parse_time": self.last_stats.parse_time if self.last_stats else 0,
            "data_sample": None,
            "errors": self.last_stats.errors if self.last_stats else [],
        }

        # Добавление образца данных
        if isinstance(data, str):
            analysis["data_sample"] = data[:500]
        elif isinstance(data, list):
            analysis["data_sample"] = data[:5]
        elif isinstance(data, dict):
            analysis["data_sample"] = dict(list(data.items())[:5])

        # Фильтрация по паттерну
        if filter_pattern and isinstance(data, str):
            lines = data.split("\n")
            filtered = [
                line for line in lines
                if filter_pattern.lower() in line.lower()
            ]
            analysis["filtered_lines"] = filtered
            analysis["filtered_count"] = len(filtered)

        return analysis

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Получение списка поддерживаемых форматов.

        Returns:
            Словарь с форматами и их расширениями.
        """
        formats = {}

        for format_name, parser_class in self.parsers.items():
            if hasattr(parser_class, "extensions"):
                formats[format_name] = parser_class.extensions

        return formats

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Получение статистики последнего парсинга.

        Returns:
            Статистика или None.
        """
        if self.last_stats:
            return self.last_stats.to_dict()
        return None
