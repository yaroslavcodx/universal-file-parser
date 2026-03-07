"""
Парсер INI формата.
"""

import configparser
from typing import Any, Dict, List, Optional, Union
from io import StringIO

from parser.base import BaseParser


class IniParser(BaseParser):
    """Парсер INI файлов."""

    extensions = [".ini", ".cfg", ".conf"]
    format_name = "ini"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        allow_no_value: bool = True,
        interpolation: bool = False,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        Парсинг INI файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            allow_no_value: Разрешить значения без значений.
            interpolation: Использовать интерполяцию.

        Returns:
            Распарсенные данные.
        """
        content = self._read_file(file_path, encoding)

        config = configparser.ConfigParser(
            allow_no_value=allow_no_value,
            interpolation=configparser.BasicInterpolation() if interpolation else None,
        )

        # Сохраняем регистр ключей
        config.optionxform = str

        config.read_string(content)

        result = {}

        for section in config.sections():
            result[section] = {}

            for key, value in config.items(section):
                result[section][key] = self._convert_value(value)

        return result

    def _convert_value(self, value: Optional[str]) -> Any:
        """
        Конвертация значения в подходящий тип.

        Args:
            value: Строковое значение.

        Returns:
            Конвертированное значение.
        """
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        # Boolean
        if value.lower() in ("true", "yes", "on", "1"):
            return True
        if value.lower() in ("false", "no", "off", "0"):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # List (разделенный запятыми)
        if "," in value and not value.startswith('"'):
            parts = [p.strip() for p in value.split(",")]
            if all(p.strip() for p in parts):
                return parts

        return value

    def save(
        self,
        data: Dict[str, Dict[str, Any]],
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение INI файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
        """
        config = configparser.ConfigParser()
        config.optionxform = str  # Сохраняем регистр

        for section, items in data.items():
            if not config.has_section(section):
                config.add_section(section)

            for key, value in items.items():
                if isinstance(value, list):
                    config.set(section, key, ", ".join(str(v) for v in value))
                elif isinstance(value, bool):
                    config.set(section, key, "true" if value else "false")
                else:
                    config.set(section, key, str(value) if value is not None else "")

        output = StringIO()
        config.write(output)

        self._write_file(file_path, output.getvalue(), encoding)

    def get_sections(self, file_path: str, encoding: str = "utf-8") -> List[str]:
        """
        Получение списка секций INI файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.

        Returns:
            Список имен секций.
        """
        data = self.parse(file_path, encoding=encoding)
        return list(data.keys())

    def get_section(
        self,
        file_path: str,
        section: str,
        encoding: str = "utf-8",
    ) -> Optional[Dict[str, Any]]:
        """
        Получение конкретной секции INI файла.

        Args:
            file_path: Путь к файлу.
            section: Имя секции.
            encoding: Кодировка.

        Returns:
            Данные секции или None.
        """
        data = self.parse(file_path, encoding=encoding)
        return data.get(section)

    def get_value(
        self,
        file_path: str,
        section: str,
        key: str,
        encoding: str = "utf-8",
        default: Any = None,
    ) -> Any:
        """
        Получение конкретного значения из INI файла.

        Args:
            file_path: Путь к файлу.
            section: Имя секции.
            key: Имя ключа.
            encoding: Кодировка.
            default: Значение по умолчанию.

        Returns:
            Значение или default.
        """
        data = self.parse(file_path, encoding=encoding)
        section_data = data.get(section, {})
        return section_data.get(key, default)

    def validate(
        self,
        file_path: str,
        encoding: str = "utf-8",
        required_sections: Optional[List[str]] = None,
        required_keys: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Валидация INI файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            required_sections: Требуемые секции.
            required_keys: Требуемые ключи по секциям.

        Returns:
            Результат валидации.
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            data = self.parse(file_path, encoding=encoding)

            # Проверка требуемых секций
            if required_sections:
                for section in required_sections:
                    if section not in data:
                        result["valid"] = False
                        result["errors"].append(f"Missing required section: [{section}]")

            # Проверка требуемых ключей
            if required_keys:
                for section, keys in required_keys.items():
                    section_data = data.get(section, {})

                    for key in keys:
                        if key not in section_data:
                            result["valid"] = False
                            result["errors"].append(
                                f"Missing required key '{key}' in section [{section}]"
                            )

        except configparser.Error as e:
            result["valid"] = False
            result["errors"].append(f"INI parse error: {str(e)}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))

        return result
