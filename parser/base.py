"""
Базовый класс для всех парсеров.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class BaseParser(ABC):
    """Абстрактный базовый класс для парсеров файлов."""

    # Расширения файлов, поддерживаемые парсером
    extensions: List[str] = []

    # Название формата
    format_name: str = "base"

    @abstractmethod
    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str, bytes]:
        """
        Парсинг файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка файла.
            **kwargs: Дополнительные параметры.

        Returns:
            Распарсенные данные.
        """
        pass

    @abstractmethod
    def save(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]], str, bytes],
        file_path: str,
        **kwargs
    ) -> None:
        """
        Сохранение данных в файл.

        Args:
            data: Данные для сохранения.
            file_path: Путь к файлу.
            **kwargs: Дополнительные параметры.
        """
        pass

    @classmethod
    def supports_extension(cls, extension: str) -> bool:
        """
        Проверка поддержки расширения.

        Args:
            extension: Расширение файла (с точкой или без).

        Returns:
            True если расширение поддерживается.
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in cls.extensions

    @classmethod
    def get_extensions(cls) -> List[str]:
        """Получить список поддерживаемых расширений."""
        return cls.extensions.copy()

    def _get_path(self, file_path: str) -> Path:
        """Преобразование пути в Path объект."""
        return Path(file_path) if isinstance(file_path, str) else file_path

    def _read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Чтение текстового файла."""
        path = self._get_path(file_path)
        with path.open("r", encoding=encoding) as f:
            return f.read()

    def _read_bytes(self, file_path: str) -> bytes:
        """Чтение бинарного файла."""
        path = self._get_path(file_path)
        with path.open("rb") as f:
            return f.read()

    def _write_file(self, file_path: str, content: str, encoding: str = "utf-8") -> None:
        """Запись текстового файла."""
        path = self._get_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding=encoding) as f:
            f.write(content)

    def _write_bytes(self, file_path: str, content: bytes) -> None:
        """Запись бинарного файла."""
        path = self._get_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(content)

    def get_info(self) -> Dict[str, Any]:
        """
        Получение информации о парсере.

        Returns:
            Информация о парсере.
        """
        return {
            "format_name": self.format_name,
            "extensions": self.extensions,
            "class_name": self.__class__.__name__,
        }
