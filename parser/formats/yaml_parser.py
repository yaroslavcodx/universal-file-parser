"""
Парсер YAML формата.
"""

import yaml
from typing import Any, Dict, List, Optional, Union

from parser.base import BaseParser


class YamlParser(BaseParser):
    """Парсер YAML файлов."""

    extensions = [".yaml", ".yml"]
    format_name = "yaml"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        safe_load: bool = True,
        **kwargs
    ) -> Union[Dict[str, Any], List[Any], str]:
        """
        Парсинг YAML файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            safe_load: Использовать безопасную загрузку.

        Returns:
            Распарсенные данные.
        """
        content = self._read_file(file_path, encoding)

        if safe_load:
            data = yaml.safe_load(content)
        else:
            data = yaml.load(content, Loader=yaml.FullLoader)

        # Пустой файл возвращает None
        if data is None:
            return {}

        return data

    def save(
        self,
        data: Union[Dict[str, Any], List[Any]],
        file_path: str,
        encoding: str = "utf-8",
        default_flow_style: bool = False,
        allow_unicode: bool = True,
        sort_keys: bool = False,
        **kwargs
    ) -> None:
        """
        Сохранение YAML файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            default_flow_style: Стиль потока.
            allow_unicode: Разрешить Unicode.
            sort_keys: Сортировать ключи.
        """
        content = yaml.dump(
            data,
            default_flow_style=default_flow_style,
            allow_unicode=allow_unicode,
            sort_keys=sort_keys,
        )

        self._write_file(file_path, content, encoding)

    def to_json(
        self,
        file_path: str,
        output_path: str,
        encoding: str = "utf-8",
        indent: int = 2,
        **kwargs
    ) -> None:
        """
        Конвертация YAML в JSON.

        Args:
            file_path: Путь к YAML файлу.
            output_path: Путь к JSON файлу.
            encoding: Кодировка.
            indent: Отступ в JSON.
        """
        import json

        data = self.parse(file_path, encoding=encoding)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def from_json(
        self,
        file_path: str,
        output_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Конвертация JSON в YAML.

        Args:
            file_path: Путь к JSON файлу.
            output_path: Путь к YAML файлу.
            encoding: Кодировка.
        """
        from parser.formats import JsonParser

        json_parser = JsonParser()
        data = json_parser.parse(file_path, encoding=encoding)

        self.save(data, output_path, encoding=encoding)

    def validate(
        self,
        file_path: str,
        encoding: str = "utf-8",
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Валидация YAML.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            schema: Схема для валидации.

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
        except yaml.YAMLError as e:
            result["valid"] = False
            result["errors"].append(f"YAML parse error: {str(e)}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))

        return result

    def merge(
        self,
        file_paths: List[str],
        output_path: Optional[str] = None,
        encoding: str = "utf-8",
        deep_merge: bool = True,
    ) -> Dict[str, Any]:
        """
        Слияние нескольких YAML файлов.

        Args:
            file_paths: Пути к файлам.
            output_path: Путь для сохранения результата.
            encoding: Кодировка.
            deep_merge: Глубокое слияние.

        Returns:
            Слитые данные.
        """
        merged = {}

        for path in file_paths:
            data = self.parse(path, encoding=encoding)

            if isinstance(data, dict):
                if deep_merge:
                    merged = self._deep_merge(merged, data)
                else:
                    merged.update(data)
            elif isinstance(data, list):
                if isinstance(merged, list):
                    merged.extend(data)
                else:
                    merged = data

        if output_path:
            self.save(merged, output_path, encoding=encoding)

        return merged

    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Глубокое слияние словарей.

        Args:
            base: Базовый словарь.
            override: Словарь для слияния.

        Returns:
            Слитый словарь.
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
