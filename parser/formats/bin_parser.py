"""
Парсер бинарных файлов.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from parser.base import BaseParser
from parser.utils import hex_dump, format_size


class BinParser(BaseParser):
    """Парсер бинарных файлов."""

    extensions = [".bin"]
    format_name = "binary"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        hex_view: bool = False,
        width: int = 16,
        max_bytes: Optional[int] = None,
        extract_strings: bool = False,
        min_string_length: int = 4,
        **kwargs
    ) -> Union[bytes, Dict[str, Any]]:
        """
        Парсинг бинарного файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            hex_view: Вернуть hex-дамп.
            width: Ширина hex-дампа.
            max_bytes: Максимум байт для чтения.
            extract_strings: Извлечь строки.
            min_string_length: Минимальная длина строки.

        Returns:
            Распарсенные данные.
        """
        data = self._read_bytes(file_path)

        if max_bytes:
            data = data[:max_bytes]

        result: Dict[str, Any] = {
            "size": len(data),
            "size_formatted": format_size(len(data)),
            "data": data,
        }

        if hex_view:
            result["hex_dump"] = hex_dump(data, width=width)

        if extract_strings:
            result["strings"] = self._extract_strings(data, min_string_length)

        # Информация о файле
        result["header"] = self._analyze_header(data)

        if hex_view:
            return result["hex_dump"]

        return result

    def _extract_strings(
        self,
        data: bytes,
        min_length: int = 4
    ) -> List[str]:
        """
        Извлечение строк из бинарных данных.

        Args:
            data: Байтовые данные.
            min_length: Минимальная длина строки.

        Returns:
            Список строк.
        """
        strings = []
        current_string = []

        for byte in data:
            if 32 <= byte < 127:
                current_string.append(chr(byte))
            else:
                if len(current_string) >= min_length:
                    strings.append("".join(current_string))
                current_string = []

        if len(current_string) >= min_length:
            strings.append("".join(current_string))

        return strings

    def _analyze_header(self, data: bytes) -> Dict[str, Any]:
        """
        Анализ заголовка файла.

        Args:
            data: Байтовые данные.

        Returns:
            Информация о заголовке.
        """
        header = data[:16] if len(data) >= 16 else data

        result = {
            "magic_bytes": header.hex(),
            "file_type": self._detect_file_type(data),
        }

        return result

    def _detect_file_type(self, data: bytes) -> str:
        """
        Определение типа файла по сигнатуре.

        Args:
            data: Байтовые данные.

        Returns:
            Тип файла.
        """
        signatures = {
            b"\x89PNG": "PNG image",
            b"\xff\xd8\xff": "JPEG image",
            b"GIF87a": "GIF image",
            b"GIF89a": "GIF image",
            b"PK\x03\x04": "ZIP archive",
            b"PK\x05\x06": "ZIP archive (empty)",
            b"\x1f\x8b": "GZIP compressed",
            b"BZh": "BZIP2 compressed",
            b"\xfd7zXZ": "XZ compressed",
            b"RIFF": "RIFF container",
            b"\x00\x00\x00": "Possible binary data",
        }

        for signature, file_type in signatures.items():
            if data.startswith(signature):
                return file_type

        return "Unknown binary"

    def save(
        self,
        data: Union[bytes, Dict[str, Any], str],
        file_path: str,
        **kwargs
    ) -> None:
        """
        Сохранение бинарного файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
        """
        if isinstance(data, dict):
            if "data" in data:
                binary_data = data["data"]
            else:
                raise ValueError("Dict data must contain 'data' key with bytes")
        elif isinstance(data, str):
            # Конвертация hex строки в байты
            binary_data = bytes.fromhex(data.replace(" ", "").replace("\n", ""))
        else:
            binary_data = data

        self._write_bytes(file_path, binary_data)

    def compare(
        self,
        file_path1: str,
        file_path2: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Сравнение двух бинарных файлов.

        Args:
            file_path1: Путь к первому файлу.
            file_path2: Путь ко второму файлу.

        Returns:
            Результат сравнения.
        """
        data1 = self._read_bytes(file_path1)
        data2 = self._read_bytes(file_path2)

        result = {
            "file1": {
                "path": file_path1,
                "size": len(data1),
                "size_formatted": format_size(len(data1)),
            },
            "file2": {
                "path": file_path2,
                "size": len(data2),
                "size_formatted": format_size(len(data2)),
            },
            "identical": data1 == data2,
            "size_diff": len(data2) - len(data1),
        }

        if not result["identical"]:
            # Поиск первого различия
            for i in range(min(len(data1), len(data2))):
                if data1[i] != data2[i]:
                    result["first_diff_offset"] = i
                    result["first_diff_file1"] = hex(data1[i])
                    result["first_diff_file2"] = hex(data2[i])
                    break
            else:
                result["first_diff_offset"] = min(len(data1), len(data2))

        return result

    def extract(
        self,
        file_path: str,
        output_dir: str,
        pattern: Optional[bytes] = None,
        **kwargs
    ) -> List[str]:
        """
        Извлечение данных из бинарного файла.

        Args:
            file_path: Путь к файлу.
            output_dir: Директория для сохранения.
            pattern: Паттерн для поиска.

        Returns:
            Список извлеченных файлов.
        """
        data = self._read_bytes(file_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        extracted_files = []

        if pattern:
            # Поиск по паттерну
            start = 0

            while True:
                pos = data.find(pattern, start)

                if pos == -1:
                    break

                # Извлечение блока данных
                block = data[pos:pos + 1024]  # Пример блока
                output_file = output_path / f"extracted_{len(extracted_files)}.bin"

                with open(output_file, "wb") as f:
                    f.write(block)

                extracted_files.append(str(output_file))
                start = pos + 1
        else:
            # Сохранение всего файла
            output_file = output_path / "extracted.bin"

            with open(output_file, "wb") as f:
                f.write(data)

            extracted_files.append(str(output_file))

        return extracted_files
