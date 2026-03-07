"""
Парсеры архивов.
"""

import zipfile
import tarfile
import gzip
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from parser.base import BaseParser


class ZipParser(BaseParser):
    """Парсер ZIP архивов."""

    extensions = [".zip"]
    format_name = "zip"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        list_only: bool = True,
        extract_path: Optional[str] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[str]]:
        """
        Парсинг ZIP архива.

        Args:
            file_path: Путь к архиву.
            encoding: Кодировка.
            list_only: Только список файлов.
            extract_path: Путь для извлечения.

        Returns:
            Информация об архиве или список файлов.
        """
        with zipfile.ZipFile(file_path, "r") as zf:
            if list_only:
                return self._get_archive_info(zf)

            if extract_path:
                zf.extractall(extract_path)
                return [str(f) for f in Path(extract_path).rglob("*")]

            return zf.namelist()

    def _get_archive_info(self, zf: zipfile.ZipFile) -> Dict[str, Any]:
        """Получение информации об архиве."""
        files = []

        for info in zf.infolist():
            file_info = {
                "filename": info.filename,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "compression_type": info.compress_type,
                "modified": info.date_time,
            }

            if info.file_size > 0:
                file_info["compression_ratio"] = (
                    1 - info.compress_size / info.file_size
                ) * 100
            else:
                file_info["compression_ratio"] = 0

            files.append(file_info)

        return {
            "total_files": len(files),
            "files": files,
            "comment": zf.comment.decode("utf-8") if zf.comment else "",
        }

    def save(
        self,
        data: Union[Dict[str, Any], List[str]],
        file_path: str,
        compression: int = zipfile.ZIP_DEFLATED,
        **kwargs
    ) -> None:
        """
        Создание ZIP архива.

        Args:
            data: Данные (список файлов или dict с данными).
            file_path: Путь к архиву.
            compression: Метод сжатия.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(file_path, "w", compression=compression) as zf:
            if isinstance(data, list):
                for file_path in data:
                    zf.write(file_path)
            elif isinstance(data, dict):
                for name, content in data.items():
                    zf.writestr(name, content)

    def extract_file(
        self,
        archive_path: str,
        file_name: str,
        output_path: str,
    ) -> bytes:
        """
        Извлечение конкретного файла из архива.

        Args:
            archive_path: Путь к архиву.
            file_name: Имя файла в архиве.
            output_path: Путь для сохранения.

        Returns:
            Содержимое файла.
        """
        with zipfile.ZipFile(archive_path, "r") as zf:
            content = zf.read(file_name)

            if output_path:
                output = Path(output_path)
                output.parent.mkdir(parents=True, exist_ok=True)

                with open(output, "wb") as f:
                    f.write(content)

            return content

    def add_files(
        self,
        archive_path: str,
        files: List[str],
        **kwargs
    ) -> None:
        """
        Добавление файлов в архив.

        Args:
            archive_path: Путь к архиву.
            files: Список файлов для добавления.
        """
        with zipfile.ZipFile(archive_path, "a") as zf:
            for file_path in files:
                zf.write(file_path)


class TarParser(BaseParser):
    """Парсер TAR архивов."""

    extensions = [".tar"]
    format_name = "tar"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        list_only: bool = True,
        extract_path: Optional[str] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[str]]:
        """
        Парсинг TAR архива.

        Args:
            file_path: Путь к архиву.
            encoding: Кодировка.
            list_only: Только список файлов.
            extract_path: Путь для извлечения.

        Returns:
            Информация об архиве или список файлов.
        """
        with tarfile.open(file_path, "r") as tf:
            if list_only:
                return self._get_archive_info(tf)

            if extract_path:
                tf.extractall(extract_path)
                return [str(f) for f in Path(extract_path).rglob("*")]

            return tf.getnames()

    def _get_archive_info(self, tf: tarfile.TarFile) -> Dict[str, Any]:
        """Получение информации об архиве."""
        files = []

        for member in tf.getmembers():
            file_info = {
                "name": member.name,
                "size": member.size,
                "type": self._get_type_name(member.type),
                "modified": member.mtime,
                "uid": member.uid,
                "gid": member.gid,
            }

            if member.isdir():
                file_info["type"] = "directory"
            elif member.isfile():
                file_info["type"] = "file"
            elif member.issym():
                file_info["type"] = "symlink"
                file_info["linkname"] = member.linkname

            files.append(file_info)

        return {
            "total_files": len(files),
            "files": files,
        }

    def _get_type_name(self, type_code: int) -> str:
        """Получение имени типа файла."""
        types = {
            tarfile.REGTYPE: "file",
            tarfile.AREGTYPE: "file",
            tarfile.DIRTYPE: "directory",
            tarfile.SYMTYPE: "symlink",
            tarfile.LNKTYPE: "hardlink",
            tarfile.CHRTYPE: "char_device",
            tarfile.BLKTYPE: "block_device",
            tarfile.FIFOTYPE: "fifo",
        }
        return types.get(type_code, "unknown")

    def save(
        self,
        data: Union[Dict[str, Any], List[str]],
        file_path: str,
        **kwargs
    ) -> None:
        """
        Создание TAR архива.

        Args:
            data: Данные (список файлов).
            file_path: Путь к архиву.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with tarfile.open(file_path, "w") as tf:
            if isinstance(data, list):
                for file_path in data:
                    tf.add(file_path)

    def extract_file(
        self,
        archive_path: str,
        member_name: str,
        output_path: str,
    ) -> Optional[bytes]:
        """
        Извлечение файла из TAR архива.

        Args:
            archive_path: Путь к архиву.
            member_name: Имя файла в архиве.
            output_path: Путь для сохранения.

        Returns:
            Содержимое файла или None.
        """
        with tarfile.open(archive_path, "r") as tf:
            member = tf.getmember(member_name)

            if member.isfile():
                f = tf.extractfile(member)

                if f:
                    content = f.read()

                    if output_path:
                        output = Path(output_path)
                        output.parent.mkdir(parents=True, exist_ok=True)

                        with open(output, "wb") as out:
                            out.write(content)

                    return content

        return None


class GzParser(BaseParser):
    """Парсер GZIP файлов."""

    extensions = [".gz", ".tgz"]
    format_name = "gzip"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        as_text: bool = True,
        **kwargs
    ) -> Union[str, bytes]:
        """
        Парсинг GZIP файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            as_text: Вернуть как текст.

        Returns:
            Распакованные данные.
        """
        with gzip.open(file_path, "rb") as gf:
            data = gf.read()

            if as_text:
                return data.decode(encoding)

            return data

    def save(
        self,
        data: Union[str, bytes],
        file_path: str,
        encoding: str = "utf-8",
        compresslevel: int = 9,
        **kwargs
    ) -> None:
        """
        Создание GZIP файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            compresslevel: Уровень сжатия.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, str):
            data = data.encode(encoding)

        with gzip.open(file_path, "wb", compresslevel=compresslevel) as gf:
            gf.write(data)

    def compress(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        compresslevel: int = 9,
    ) -> str:
        """
        Сжатие файла.

        Args:
            input_path: Путь к входному файлу.
            output_path: Путь к выходному файлу.
            compresslevel: Уровень сжатия.

        Returns:
            Путь к сжатому файлу.
        """
        if output_path is None:
            output_path = f"{input_path}.gz"

        with open(input_path, "rb") as f_in:
            with gzip.open(output_path, "wb", compresslevel=compresslevel) as f_out:
                shutil.copyfileobj(f_in, f_out)

        return output_path

    def decompress(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Распаковка файла.

        Args:
            input_path: Путь к входному файлу.
            output_path: Путь к выходному файлу.

        Returns:
            Путь к распакованному файлу.
        """
        if output_path is None:
            output_path = input_path[:-3] if input_path.endswith(".gz") else f"{input_path}.decompressed"

        with gzip.open(input_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        return output_path

    def get_info(self, file_path: str) -> Dict[str, Any]:
        """
        Получение информации о GZIP файле.

        Args:
            file_path: Путь к файлу.

        Returns:
            Информация о файле.
        """
        with gzip.open(file_path, "rb") as gf:
            # Читаем немного данных для получения информации
            data = gf.read(1024)

        with open(file_path, "rb") as f:
            header = f.read(10)

        return {
            "compressed_size": Path(file_path).stat().st_size,
            "magic": header[:2].hex(),
            "compression_method": header[2] if len(header) > 2 else None,
            "sample_data": data[:100],
        }
