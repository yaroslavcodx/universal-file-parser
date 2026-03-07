"""
Парсер ODS формата.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import odf.opendocument
import odf.table
import odf.text
from parser.base import BaseParser


class OdsParser(BaseParser):
    """Парсер ODS файлов."""

    extensions = [".ods"]
    format_name = "ods"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        sheet: Optional[Union[str, int]] = None,
        has_header: bool = True,
        skip_empty_rows: bool = True,
        **kwargs
    ) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Парсинг ODS файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            sheet: Имя или индекс листа (None = все листы).
            has_header: Есть ли заголовок.
            skip_empty_rows: Пропускать пустые строки.

        Returns:
            Список словарей или словарь по листам.
        """
        doc = odf.opendocument.load(file_path)

        tables = doc.getElementsByType(odf.table.Table)

        if sheet is not None:
            # Один лист
            if isinstance(sheet, int):
                if sheet >= len(tables):
                    raise ValueError(f"Sheet index {sheet} out of range")
                table = tables[sheet]
            else:
                table = None

                for t in tables:
                    if t.getAttribute("name") == sheet:
                        table = t
                        break

                if table is None:
                    raise ValueError(f"Sheet '{sheet}' not found")

            data = self._parse_table(table, has_header, skip_empty_rows)
            return data
        else:
            # Все листы
            result = {}

            for table in tables:
                name = table.getAttribute("name")
                result[name] = self._parse_table(table, has_header, skip_empty_rows)

            return result

    def _parse_table(
        self,
        table,
        has_header: bool = True,
        skip_empty_rows: bool = True,
    ) -> List[Dict[str, Any]]:
        """Парсинг таблицы."""
        rows = table.getElementsByType(odf.table.TableRow)

        data_rows = []

        for row in rows:
            cells = row.getElementsByType(odf.table.TableCell)
            row_data = []

            for cell in cells:
                # Получение значения ячейки
                value = self._get_cell_value(cell)
                repeat = cell.getAttribute("numberrepeatedcolumns")

                if repeat:
                    repeat_count = int(repeat)
                else:
                    repeat_count = 1

                row_data.extend([value] * repeat_count)

            if skip_empty_rows and not any(row_data):
                continue

            data_rows.append(row_data)

        if not data_rows:
            return []

        # Заголовки
        if has_header and data_rows:
            headers = [str(h) if h is not None else f"column_{i}" for i, h in enumerate(data_rows[0])]
            data_rows = data_rows[1:]
        else:
            max_cols = max(len(row) for row in data_rows)
            headers = [f"column_{i}" for i in range(max_cols)]

        # Конвертация в словари
        result = []

        for row in data_rows:
            row_dict = {}

            for i, value in enumerate(row):
                if i < len(headers):
                    row_dict[headers[i]] = value
                else:
                    row_dict[f"column_{i}"] = value

            result.append(row_dict)

        return result

    def _get_cell_value(self, cell) -> Any:
        """Получение значения ячейки."""
        # Проверка типа значения
        value_type = cell.getAttribute("valuetype")

        if value_type == "boolean":
            value = cell.getAttribute("booleanvalue")
            return value == "true"

        if value_type == "float":
            value = cell.getAttribute("value")
            if value:
                try:
                    return float(value)
                except ValueError:
                    pass

        if value_type == "currency":
            value = cell.getAttribute("value")
            if value:
                try:
                    return float(value)
                except ValueError:
                    pass

        # Текстовое значение
        text_nodes = cell.getElementsByType(odf.text.P)

        if text_nodes:
            return "".join(node.textContent for node in text_nodes)

        return None

    def save(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]],
        file_path: str,
        encoding: str = "utf-8",
        sheet_name: str = "Sheet1",
        **kwargs
    ) -> None:
        """
        Сохранение ODS файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            sheet_name: Имя листа.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        doc = odf.opendocument.OpenDocumentSpreadsheet()

        if isinstance(data, dict):
            # Несколько листов
            for name, sheet_data in data.items():
                table = self._create_table(name, sheet_data)
                doc.spreadsheet.addElement(table)
        else:
            # Один лист
            table = self._create_table(sheet_name, data)
            doc.spreadsheet.addElement(table)

        doc.save(file_path)

    def _create_table(self, name: str, data: List[Dict[str, Any]]):
        """Создание таблицы."""
        table = odf.table.Table(name=name)

        if not data:
            return table

        # Заголовки
        headers = list(data[0].keys())
        header_row = odf.table.TableRow()

        for header in headers:
            cell = odf.table.TableCell()
            p = odf.text.P(text=str(header))
            cell.addElement(p)
            header_row.addElement(cell)

        table.addElement(header_row)

        # Данные
        for row in data:
            table_row = odf.table.TableRow()

            for header in headers:
                value = row.get(header)
                cell = odf.table.TableCell()
                p = odf.text.P(text=str(value) if value is not None else "")
                cell.addElement(p)
                table_row.addElement(cell)

            table.addElement(table_row)

        return table

    def get_info(self, file_path: str) -> Dict[str, Any]:
        """
        Получение информации о файле.

        Args:
            file_path: Путь к файлу.

        Returns:
            Информация о файле.
        """
        doc = odf.opendocument.load(file_path)
        tables = doc.getElementsByType(odf.table.Table)

        info = {
            "sheets": [],
            "total_sheets": len(tables),
        }

        for table in tables:
            name = table.getAttribute("name")
            rows = table.getElementsByType(odf.table.TableRow)

            sheet_info = {
                "name": name,
                "rows": len(rows),
            }

            info["sheets"].append(sheet_info)

        return info

    def to_csv(
        self,
        file_path: str,
        output_path: str,
        sheet: Optional[Union[str, int]] = None,
        delimiter: str = ",",
        **kwargs
    ) -> None:
        """
        Конвертация ODS в CSV.

        Args:
            file_path: Путь к ODS файлу.
            output_path: Путь к CSV файлу.
            sheet: Имя или индекс листа.
            delimiter: Разделитель.
        """
        import csv

        data = self.parse(file_path, sheet=sheet, has_header=True)

        if not data:
            return

        # Если список листов
        if isinstance(data, dict):
            for name, sheet_data in data.items():
                out_path = f"{output_path}_{name}.csv"
                self._write_csv(sheet_data, out_path, delimiter)
        else:
            self._write_csv(data, output_path, delimiter)

    def _write_csv(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        delimiter: str = ",",
    ) -> None:
        """Запись CSV файла."""
        import csv

        if not data:
            return

        headers = list(data[0].keys())

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
