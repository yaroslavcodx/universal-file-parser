"""
Парсеры текстовых форматов.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import re

from parser.base import BaseParser


class TextParser(BaseParser):
    """Парсер текстовых файлов."""

    extensions = [".txt"]
    format_name = "text"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        split_lines: bool = False,
        **kwargs
    ) -> Union[str, List[str]]:
        """
        Парсинг текстового файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            split_lines: Разбить на строки.

        Returns:
            Содержимое файла.
        """
        content = self._read_file(file_path, encoding)

        if split_lines:
            return content.split("\n")

        return content

    def save(
        self,
        data: Union[str, List[str]],
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение текстового файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
        """
        if isinstance(data, list):
            content = "\n".join(str(item) for item in data)
        else:
            content = str(data)

        self._write_file(file_path, content, encoding)


class MarkdownParser(BaseParser):
    """Парсер Markdown файлов."""

    extensions = [".md", ".markdown"]
    format_name = "markdown"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        extract_headers: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Парсинг Markdown файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            extract_headers: Извлечь заголовки.

        Returns:
            Содержимое файла или структура с заголовками.
        """
        content = self._read_file(file_path, encoding)

        if extract_headers:
            headers = []
            for line in content.split("\n"):
                match = re.match(r"^(#{1,6})\s+(.+)$", line)
                if match:
                    headers.append({
                        "level": len(match.group(1)),
                        "text": match.group(2),
                    })

            return {
                "content": content,
                "headers": headers,
                "links": self._extract_links(content),
                "code_blocks": self._extract_code_blocks(content),
            }

        return content

    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """Извлечение ссылок из Markdown."""
        links = []
        pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        for match in re.finditer(pattern, content):
            links.append({
                "text": match.group(1),
                "url": match.group(2),
            })

        return links

    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Извлечение блоков кода."""
        blocks = []
        pattern = r"```(\w*)\n(.*?)```"

        for match in re.finditer(pattern, content, re.DOTALL):
            blocks.append({
                "language": match.group(1) or "text",
                "code": match.group(2).strip(),
            })

        return blocks

    def save(
        self,
        data: Union[str, Dict[str, Any]],
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение Markdown файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
        """
        if isinstance(data, dict):
            content = data.get("content", "")
        else:
            content = str(data)

        self._write_file(file_path, content, encoding)


class LogParser(BaseParser):
    """Парсер лог-файлов."""

    extensions = [".log"]
    format_name = "log"

    # Паттерны для распространенных форматов логов
    LOG_PATTERNS = {
        "generic": r"^(?P<timestamp>.*?)?\s*(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)?\s*(?P<message>.*)$",
        "apache": r'^(?P<ip>[\d.]+)\s+-\s+-\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<request>[^"]+)"\s+(?P<status>\d+)\s+(?P<size>\d+|-)',
        "nginx": r'^(?P<ip>[\d.]+)\s+-\s+-\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<request>[^"]+)"\s+(?P<status>\d+)\s+(?P<size>\d+)\s+"(?P<referrer>[^"]+)"\s+"(?P<user_agent>[^"]+)"',
    }

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        pattern: str = "generic",
        parse_levels: bool = True,
        **kwargs
    ) -> Union[List[str], List[Dict[str, Any]]]:
        """
        Парсинг лог-файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            pattern: Паттерн для парсинга.
            parse_levels: Парсить уровни логов.

        Returns:
            Список строк или структурированные записи.
        """
        content = self._read_file(file_path, encoding)
        lines = content.split("\n")

        if not parse_levels:
            return [line for line in lines if line.strip()]

        # Парсинг с извлечением уровней
        entries = []
        level_pattern = re.compile(
            r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b",
            re.IGNORECASE
        )

        for line in lines:
            if not line.strip():
                continue

            match = level_pattern.search(line)
            level = match.group(1).upper() if match else "UNKNOWN"

            entries.append({
                "raw": line,
                "level": level,
                "timestamp": self._extract_timestamp(line),
            })

        return entries

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Извлечение временной метки из строки лога."""
        patterns = [
            r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
            r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}",
            r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)

        return None

    def save(
        self,
        data: Union[List[str], List[Dict[str, Any]]],
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение лог-файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
        """
        if isinstance(data[0], dict) if data else False:
            lines = [entry.get("raw", str(entry)) for entry in data]
        else:
            lines = [str(line) for line in data]

        content = "\n".join(lines)
        self._write_file(file_path, content, encoding)

    def get_statistics(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Статистика по лог-записям.

        Args:
            entries: Записи лога.

        Returns:
            Статистика.
        """
        stats = {
            "total": len(entries),
            "by_level": {},
        }

        for entry in entries:
            level = entry.get("level", "UNKNOWN")
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

        return stats
