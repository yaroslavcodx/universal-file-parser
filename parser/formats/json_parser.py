"""
Парсер JSON формата.
"""

import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from parser.base import BaseParser


class JsonParser(BaseParser):
    """Парсер JSON файлов."""

    extensions = [".json", ".geojson"]
    format_name = "json"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        flatten: bool = False,
        max_depth: int = 10,
        **kwargs
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Парсинг JSON файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            flatten: Flatten вложенные структуры.
            max_depth: Максимальная глубина для flatten.

        Returns:
            Распарсенные данные.
        """
        content = self._read_file(file_path, encoding)
        data = json.loads(content)

        if flatten:
            return self._flatten_json(data, max_depth=max_depth)

        return data

    def _flatten_json(
        self,
        data: Union[Dict, List],
        parent_key: str = "",
        sep: str = ".",
        depth: int = 0,
        max_depth: int = 10
    ) -> Union[Dict, List]:
        """
        Flatten вложенной JSON структуры.

        Args:
            data: Данные.
            parent_key: Родительский ключ.
            sep: Разделитель ключей.
            depth: Текущая глубина.
            max_depth: Максимальная глубина.

        Returns:
            Flatten данные.
        """
        if depth >= max_depth:
            return data

        if isinstance(data, dict):
            items = {}

            for key, value in data.items():
                new_key = f"{parent_key}{sep}{key}" if parent_key else key

                if isinstance(value, (dict, list)):
                    flattened = self._flatten_json(
                        value, new_key, sep, depth + 1, max_depth
                    )

                    if isinstance(flattened, dict):
                        items.update(flattened)
                    else:
                        items[new_key] = flattened
                else:
                    items[new_key] = value

            return items

        elif isinstance(data, list):
            items = {}

            for i, value in enumerate(data):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)

                if isinstance(value, (dict, list)):
                    flattened = self._flatten_json(
                        value, new_key, sep, depth + 1, max_depth
                    )

                    if isinstance(flattened, dict):
                        items.update(flattened)
                    else:
                        items[new_key] = flattened
                else:
                    items[new_key] = value

            return items

        return data

    def save(
        self,
        data: Union[Dict[str, Any], List[Any]],
        file_path: str,
        encoding: str = "utf-8",
        indent: int = 2,
        ensure_ascii: bool = False,
        sort_keys: bool = False,
        **kwargs
    ) -> None:
        """
        Сохранение JSON файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            indent: Отступ.
            ensure_ascii: Экранировать ASCII.
            sort_keys: Сортировать ключи.
        """
        content = json.dumps(
            data,
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
        )

        self._write_file(file_path, content, encoding)

    def validate(
        self,
        file_path: str,
        schema: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        Валидация JSON.

        Args:
            file_path: Путь к файлу.
            schema: JSON Schema для валидации.
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
            content = self._read_file(file_path, encoding)
            data = json.loads(content)

            # Базовая валидация структуры
            if schema:
                result.update(self._validate_schema(data, schema))

        except json.JSONDecodeError as e:
            result["valid"] = False
            result["errors"].append(f"JSON parse error: {str(e)}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))

        return result

    def _validate_schema(
        self,
        data: Any,
        schema: Dict[str, Any],
        path: str = ""
    ) -> Dict[str, Any]:
        """
        Простая валидация по схеме.

        Args:
            data: Данные.
            schema: Схема.
            path: Путь к текущему элементу.

        Returns:
            Результат валидации.
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        schema_type = schema.get("type")

        if schema_type:
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict,
                "null": type(None),
            }

            expected_type = type_map.get(schema_type)

            if expected_type and not isinstance(data, expected_type):
                result["valid"] = False
                result["errors"].append(
                    f"Type mismatch at '{path}': expected {schema_type}, "
                    f"got {type(data).__name__}"
                )

        # Проверка required полей
        if schema_type == "object" and isinstance(data, dict):
            required = schema.get("required", [])

            for field in required:
                if field not in data:
                    result["valid"] = False
                    field_path = f"{path}.{field}" if path else field
                    result["errors"].append(f"Missing required field: {field_path}")

        return result

    def merge(
        self,
        file_paths: List[str],
        output_path: Optional[str] = None,
        encoding: str = "utf-8",
        merge_key: Optional[str] = None,
    ) -> Union[Dict, List]:
        """
        Слияние нескольких JSON файлов.

        Args:
            file_paths: Пути к файлам.
            output_path: Путь для сохранения результата.
            encoding: Кодировка.
            merge_key: Ключ для слияния объектов.

        Returns:
            Слитые данные.
        """
        all_data = []

        for path in file_paths:
            data = self.parse(path, encoding=encoding)

            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)

        if merge_key and all_data and isinstance(all_data[0], dict):
            # Слияние по ключу
            merged = {}

            for item in all_data:
                key_value = item.get(merge_key)

                if key_value not in merged:
                    merged[key_value] = item
                else:
                    merged[key_value].update(item)

            result = list(merged.values())
        else:
            result = all_data

        if output_path:
            self.save(result, output_path, encoding=encoding)

        return result
