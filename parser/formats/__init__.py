"""
Парсеры для различных форматов файлов.
"""

from parser.formats.text_parser import TextParser, MarkdownParser, LogParser
from parser.formats.csv_parser import CsvParser, TsvParser
from parser.formats.json_parser import JsonParser
from parser.formats.yaml_parser import YamlParser
from parser.formats.toml_parser import TomlParser
from parser.formats.ini_parser import IniParser
from parser.formats.xml_parser import XmlParser
from parser.formats.html_parser import HtmlParser
from parser.formats.xlsx_parser import XlsxParser
from parser.formats.ods_parser import OdsParser
from parser.formats.bin_parser import BinParser
from parser.formats.archive_parser import ZipParser, TarParser, GzParser

__all__ = [
    "TextParser",
    "MarkdownParser",
    "LogParser",
    "CsvParser",
    "TsvParser",
    "JsonParser",
    "YamlParser",
    "TomlParser",
    "IniParser",
    "XmlParser",
    "HtmlParser",
    "XlsxParser",
    "OdsParser",
    "BinParser",
    "ZipParser",
    "TarParser",
    "GzParser",
    "get_parser_by_format",
    "get_all_parsers",
    "get_parser_by_extension",
]

# Маппинг форматов к классам парсеров
FORMAT_PARSERS = {
    "text": TextParser,
    "markdown": MarkdownParser,
    "log": LogParser,
    "csv": CsvParser,
    "tsv": TsvParser,
    "json": JsonParser,
    "geojson": JsonParser,
    "yaml": YamlParser,
    "toml": TomlParser,
    "ini": IniParser,
    "xml": XmlParser,
    "html": HtmlParser,
    "xlsx": XlsxParser,
    "ods": OdsParser,
    "binary": BinParser,
    "zip": ZipParser,
    "tar": TarParser,
    "gzip": GzParser,
}


def get_parser_by_format(format_name: str):
    """
    Получение класса парсера по названию формата.

    Args:
        format_name: Название формата.

    Returns:
        Класс парсера или None.
    """
    return FORMAT_PARSERS.get(format_name.lower())


def get_all_parsers() -> dict:
    """
    Получение всех доступных парсеров.

    Returns:
        Словарь с парсерами.
    """
    return FORMAT_PARSERS.copy()


def get_parser_by_extension(extension: str):
    """
    Получение класса парсера по расширению файла.

    Args:
        extension: Расширение файла.

    Returns:
        Класс парсера или None.
    """
    ext = extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"

    extension_map = {
        ".txt": TextParser,
        ".md": MarkdownParser,
        ".log": LogParser,
        ".csv": CsvParser,
        ".tsv": TsvParser,
        ".json": JsonParser,
        ".geojson": JsonParser,
        ".yaml": YamlParser,
        ".yml": YamlParser,
        ".toml": TomlParser,
        ".ini": IniParser,
        ".xml": XmlParser,
        ".html": HtmlParser,
        ".htm": HtmlParser,
        ".xlsx": XlsxParser,
        ".xls": XlsxParser,
        ".ods": OdsParser,
        ".bin": BinParser,
        ".zip": ZipParser,
        ".tar": TarParser,
        ".gz": GzParser,
        ".tgz": GzParser,
    }

    return extension_map.get(ext)
