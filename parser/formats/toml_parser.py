"""
Парсер TOML формата.
"""

import tomli
import tomli_w
from typing import Any, Dict, List, Optional, Union

from parser.base import BaseParser


class TomlParser(BaseParser):
    """Парсер TOML файлов."""

    extensions = [".toml"]
    format_name = "toml"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Парсинг TOML файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.

        Returns:
            Распарсенные данные.
        """
        content_bytes = self._read_bytes(file_path)
        data = tomli.loads(content_bytes.decode(encoding))
        return data

    def save(
        self,
        data: Dict[str, Any],
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение TOML файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
        """
        content = tomli_w.dumps(data)
        self._write_file(file_path, content, encoding)

    def validate(
        self,
        file_path: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        Валидация TOML.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.

        Returns:
            Результат валидации.
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            self.parse(file_path, encoding=encoding)
        except tomli.TOMLDecodeError as e:
            result["valid"] = False
            result["errors"].append(f"TOML parse error: {str(e)}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))

        return result

    def get_sections(self, data: Dict[str, Any]) -> List[str]:
        """
        Получение списка секций TOML.

        Args:
            data: Распарсенные данные.

        Returns:
            Список имен секций.
        """
        sections = []

        def find_sections(d: Dict, prefix: str = ""):
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key

                if isinstance(value, dict):
                    sections.append(full_key)
                    find_sections(value, full_key)

        find_sections(data)
        return sections

    def flatten(
        self,
        data: Dict[str, Any],
        sep: str = "."
    ) -> Dict[str, Any]:
        """
        Flatten вложенной TOML структуры.

        Args:
            data: Данные.
            sep: Разделитель.

        Returns:
            Flatten данные.
        """
        result = {}

        def _flatten(d: Dict, parent_key: str = ""):
            for key, value in d.items():
                new_key = f"{parent_key}{sep}{key}" if parent_key else key

                if isinstance(value, dict):
                    _flatten(value, new_key)
                else:
                    result[new_key] = value

        _flatten(data)
        return result
