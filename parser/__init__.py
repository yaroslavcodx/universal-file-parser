"""
Universal File Parser - Универсальный парсер файлов.

Поддерживает парсинг, конвертацию и анализ различных типов файлов.
"""

from parser.base import BaseParser
from parser.parser import FileParser
from parser.utils import detect_format, detect_encoding

__version__ = "1.0.0"
__all__ = [
    "BaseParser",
    "FileParser",
    "detect_format",
    "detect_encoding",
]
