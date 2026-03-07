"""
Утилиты для парсера.
"""

import re
import chardet
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime


# Магические байты для определения форматов
MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"PK\x03\x04": "zip",
    b"PK\x05\x06": "zip",
    b"\x1f\x8b": "gzip",
    b"BZh": "bzip2",
    b"\xfd7zXZ": "xz",
    b"ustar": "tar",
    b"<?xml": "xml",
    b"<?XML": "xml",
    b"{": "json",
    b"[": "json",
    b"#": "text",
    b"<!DOCTYPE": "html",
    b"<html": "html",
    b"<HTML": "html",
}

# Расширения для форматов
EXTENSION_MAP = {
    ".txt": "text",
    ".md": "markdown",
    ".csv": "csv",
    ".tsv": "tsv",
    ".json": "json",
    ".geojson": "geojson",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".xml": "xml",
    ".html": "html",
    ".htm": "html",
    ".log": "log",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".ods": "ods",
    ".bin": "binary",
    ".zip": "zip",
    ".tar": "tar",
    ".gz": "gzip",
    ".tgz": "gzip",
}


def detect_format(file_path: str) -> Optional[str]:
    """
    Определение формата файла по расширению и содержимому.

    Args:
        file_path: Путь к файлу.

    Returns:
        Название формата или None.
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    # Сначала пробуем по расширению
    if extension in EXTENSION_MAP:
        return EXTENSION_MAP[extension]

    # Если не нашли, пробуем по магическим байтам
    try:
        with path.open("rb") as f:
            header = f.read(512)

            for magic, format_name in MAGIC_BYTES.items():
                if header.startswith(magic):
                    return format_name

            # Пробуем определить по содержимому
            try:
                content = header.decode("utf-8")

                if content.strip().startswith("{") or content.strip().startswith("["):
                    return "json"

                if content.strip().startswith("<?xml") or content.strip().startswith("<"):
                    return "xml"

                if re.search(r"<html|<body|<head", content, re.IGNORECASE):
                    return "html"

                # Проверка на YAML
                if re.search(r"^\w+:\s*", content, re.MULTILINE):
                    return "yaml"

            except UnicodeDecodeError:
                pass

    except (IOError, OSError):
        pass

    return None


def detect_encoding(file_path: str) -> str:
    """
    Определение кодировки файла.

    Args:
        file_path: Путь к файлу.

    Returns:
        Название кодировки.
    """
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)

            if result["encoding"] and result["confidence"] > 0.7:
                return result["encoding"]

    except (IOError, OSError):
        pass

    # Кодировки по умолчанию
    common_encodings = ["utf-8", "windows-1251", "utf-16"]

    for encoding in common_encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                f.read(1000)
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    return "utf-8"


def format_size(size_bytes: int) -> str:
    """
    Форматирование размера файла.

    Args:
        size_bytes: Размер в байтах.

    Returns:
        Отформатированная строка.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def format_datetime(dt: Optional[datetime] = None) -> str:
    """
    Форматирование даты и времени.

    Args:
        dt: Дата и время.

    Returns:
        Отформатированная строка.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезка строки до максимальной длины.

    Args:
        s: Строка.
        max_length: Максимальная длина.
        suffix: Суффикс.

    Returns:
        Обрезанная строка.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def hex_dump(data: bytes, width: int = 16) -> str:
    """
    Создание hex-дампа данных.

    Args:
        data: Байтовые данные.
        width: Ширина строки.

    Returns:
        Hex-дамп в виде строки.
    """
    result = []

    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(
            chr(b) if 32 <= b < 127 else "." for b in chunk
        )
        result.append(
            f"{i:08x}  {hex_part:<{width * 3}}  |{ascii_part}|"
        )

    return "\n".join(result)


def filter_data(
    data: Union[Dict, List],
    filter_keys: Optional[List[str]] = None,
    regex: Optional[str] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> Union[Dict, List]:
    """
    Фильтрация данных.

    Args:
        data: Данные для фильтрации.
        filter_keys: Ключи для фильтрации.
        regex: Регулярное выражение.
        start_line: Начальная строка.
        end_line: Конечная строка.

    Returns:
        Отфильтрованные данные.
    """
    result = data

    # Фильтрация по ключам
    if filter_keys and isinstance(data, dict):
        result = {k: v for k, v in data.items() if k in filter_keys}

    # Фильтрация по диапазону строк
    if isinstance(data, list):
        if start_line is not None or end_line is not None:
            start = start_line or 0
            end = end_line or len(data)
            result = data[start:end]

    # Фильтрация по regex
    if regex:
        pattern = re.compile(regex)

        if isinstance(result, str):
            lines = result.split("\n")
            filtered = [line for line in lines if pattern.search(line)]
            result = "\n".join(filtered)

        elif isinstance(result, list):
            result = [
                item for item in result
                if any(pattern.search(str(v)) for v in item.values())
                if isinstance(item, dict)
            ] or [
                item for item in result if pattern.search(str(item))
            ]

    return result


class ParseStats:
    """Статистика парсинга."""

    def __init__(self):
        self.file_path: str = ""
        self.format: str = ""
        self.encoding: str = ""
        self.file_size: int = 0
        self.parse_time: float = 0
        self.records_count: int = 0
        self.errors_count: int = 0
        self.errors: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def start(self, file_path: str):
        """Начало парсинга."""
        self.start_time = datetime.now()
        self.file_path = file_path
        self.file_size = Path(file_path).stat().st_size

    def end(self):
        """Завершение парсинга."""
        self.end_time = datetime.now()
        if self.start_time:
            self.parse_time = (self.end_time - self.start_time).total_seconds()

    def add_error(self, error: str):
        """Добавление ошибки."""
        self.errors.append(error)
        self.errors_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "file_path": self.file_path,
            "format": self.format,
            "encoding": self.encoding,
            "file_size": format_size(self.file_size),
            "parse_time": f"{self.parse_time:.3f}s",
            "records_count": self.records_count,
            "errors_count": self.errors_count,
            "errors": self.errors,
        }

    def __str__(self) -> str:
        """Строковое представление."""
        lines = [
            f"Файл: {self.file_path}",
            f"Формат: {self.format}",
            f"Кодировка: {self.encoding}",
            f"Размер: {format_size(self.file_size)}",
            f"Время парсинга: {self.parse_time:.3f}s",
            f"Записей: {self.records_count}",
            f"Ошибок: {self.errors_count}",
        ]
        if self.errors:
            lines.append("Ошибки:")
            for error in self.errors:
                lines.append(f"  - {error}")
        return "\n".join(lines)
