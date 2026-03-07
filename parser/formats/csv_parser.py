"""
Парсеры CSV и TSV форматов.
"""

import csv
import json
from typing import Any, Dict, List, Optional, Union
from io import StringIO

from parser.base import BaseParser


class CsvParser(BaseParser):
    """Парсер CSV файлов."""

    extensions = [".csv"]
    format_name = "csv"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        delimiter: str = ",",
        has_header: bool = True,
        skip_empty: bool = True,
        **kwargs
    ) -> Union[List[Dict[str, Any]], List[List[Any]]]:
        """
        Парсинг CSV файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            delimiter: Разделитель.
            has_header: Есть ли заголовок.
            skip_empty: Пропускать пустые строки.

        Returns:
            Список словарей или списков.
        """
        content = self._read_file(file_path, encoding)
        reader = csv.reader(StringIO(content), delimiter=delimiter)

        rows = list(reader)

        if skip_empty:
            rows = [row for row in rows if any(cell.strip() for cell in row)]

        if not rows:
            return []

        if has_header and len(rows) > 0:
            headers = rows[0]
            data = []

            for row in rows[1:]:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        key = headers[i].strip()
                        row_dict[key] = self._convert_value(value)
                    else:
                        row_dict[f"column_{i}"] = self._convert_value(value)
                data.append(row_dict)

            return data
        else:
            return [
                [self._convert_value(cell) for cell in row]
                for row in rows
            ]

    def _convert_value(self, value: str) -> Any:
        """
        Конвертация значения в подходящий тип.

        Args:
            value: Строковое значение.

        Returns:
            Конвертированное значение.
        """
        value = value.strip()

        if not value:
            return None

        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
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

        return value

    def save(
        self,
        data: Union[List[Dict[str, Any]], List[List[Any]]],
        file_path: str,
        encoding: str = "utf-8",
        delimiter: str = ",",
        include_header: bool = True,
        **kwargs
    ) -> None:
        """
        Сохранение CSV файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            delimiter: Разделитель.
            include_header: Включать заголовок.
        """
        if not data:
            self._write_file(file_path, "", encoding)
            return

        output = StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        if isinstance(data[0], dict):
            # Список словарей
            headers = list(data[0].keys())

            if include_header:
                writer.writerow(headers)

            for row in data:
                writer.writerow([row.get(h, "") for h in headers])
        else:
            # Список списков
            for row in data:
                writer.writerow(row)

        self._write_file(file_path, output.getvalue(), encoding)

    def to_json(
        self,
        file_path: str,
        output_path: str,
        encoding: str = "utf-8",
        indent: int = 2,
        **kwargs
    ) -> None:
        """
        Конвертация CSV в JSON.

        Args:
            file_path: Путь к CSV файлу.
            output_path: Путь к JSON файлу.
            encoding: Кодировка.
            indent: Отступ в JSON.
        """
        data = self.parse(file_path, encoding=encoding, **kwargs)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)


class TsvParser(CsvParser):
    """Парсер TSV файлов (Tab-Separated Values)."""

    extensions = [".tsv"]
    format_name = "tsv"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        has_header: bool = True,
        **kwargs
    ) -> Union[List[Dict[str, Any]], List[List[Any]]]:
        """
        Парсинг TSV файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            has_header: Есть ли заголовок.

        Returns:
            Список словарей или списков.
        """
        return super().parse(
            file_path,
            encoding=encoding,
            delimiter="\t",
            has_header=has_header,
            **kwargs
        )

    def save(
        self,
        data: Union[List[Dict[str, Any]], List[List[Any]]],
        file_path: str,
        encoding: str = "utf-8",
        include_header: bool = True,
        **kwargs
    ) -> None:
        """
        Сохранение TSV файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            include_header: Включать заголовок.
        """
        super().save(
            data,
            file_path,
            encoding=encoding,
            delimiter="\t",
            include_header=include_header,
            **kwargs
        )
