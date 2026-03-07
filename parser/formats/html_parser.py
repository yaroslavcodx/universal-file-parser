"""
Парсер HTML формата.
"""

import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from parser.base import BaseParser


class HtmlContentParser(HTMLParser):
    """Парсер содержимого HTML."""

    def __init__(self):
        super().__init__()
        self.text_content = []
        self.current_tag = None
        self.tags_content: Dict[str, List[str]] = {}
        self.links = []
        self.images = []
        self.headings = []
        self.in_heading = False
        self.heading_level = 0
        self.current_heading = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        self.current_tag = tag

        attrs_dict = dict(attrs)

        if tag == "a":
            href = attrs_dict.get("href", "")
            text = ""
            self.links.append({"href": href, "text": ""})
        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt", ""),
            })
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.in_heading = True
            self.heading_level = int(tag[1])
            self.current_heading = ""

    def handle_endtag(self, tag: str):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.in_heading = False
            if self.current_heading.strip():
                self.headings.append({
                    "level": self.heading_level,
                    "text": self.current_heading.strip(),
                })
            self.heading_level = 0
            self.current_heading = ""

        self.current_tag = None

    def handle_data(self, data: str):
        if data.strip():
            self.text_content.append(data.strip())

            if self.in_heading:
                self.current_heading += data

            if self.links and self.current_tag == "a":
                self.links[-1]["text"] += data


class HtmlParser(BaseParser):
    """Парсер HTML файлов."""

    extensions = [".html", ".htm"]
    format_name = "html"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        extract_text: bool = True,
        extract_links: bool = False,
        extract_images: bool = False,
        extract_headings: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Парсинг HTML файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            extract_text: Извлечь текст.
            extract_links: Извлечь ссылки.
            extract_images: Извлечь изображения.
            extract_headings: Извлечь заголовки.

        Returns:
            Распарсенные данные.
        """
        content = self._read_file(file_path, encoding)

        if not any([extract_text, extract_links, extract_images, extract_headings]):
            return content

        parser = HtmlContentParser()
        parser.feed(content)

        result = {}

        if extract_text:
            result["text"] = " ".join(parser.text_content)

        if extract_links:
            result["links"] = parser.links

        if extract_images:
            result["images"] = parser.images

        if extract_headings:
            result["headings"] = parser.headings

        result["html"] = content

        return result

    def save(
        self,
        data: Union[str, Dict[str, Any]],
        file_path: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> None:
        """
        Сохранение HTML файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
        """
        if isinstance(data, dict):
            content = data.get("html", str(data))
        else:
            content = str(data)

        self._write_file(file_path, content, encoding)

    def to_markdown(
        self,
        file_path: str,
        output_path: str,
        encoding: str = "utf-8",
    ) -> str:
        """
        Конвертация HTML в Markdown.

        Args:
            file_path: Путь к HTML файлу.
            output_path: Путь к Markdown файлу.
            encoding: Кодировка.

        Returns:
            Markdown содержимое.
        """
        content = self._read_file(file_path, encoding)
        markdown = self._html_to_markdown(content)

        self._write_file(output_path, markdown, encoding)

        return markdown

    def _html_to_markdown(self, html: str) -> str:
        """
        Простая конвертация HTML в Markdown.

        Args:
            html: HTML содержимое.

        Returns:
            Markdown содержимое.
        """
        md = html

        # Заголовки
        for i in range(6, 0, -1):
            pattern = f"<h{i}[^>]*>(.*?)</h{i}>"
            replacement = "#" * i + r" \1"
            md = re.sub(pattern, replacement, md, flags=re.IGNORECASE | re.DOTALL)

        # Жирный текст
        md = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", md, flags=re.IGNORECASE | re.DOTALL)

        # Курсив
        md = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", md, flags=re.IGNORECASE | re.DOTALL)

        # Ссылки
        md = re.sub(
            r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            r"[\2](\1)",
            md,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Изображения
        md = re.sub(
            r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?>',
            r"![\2](\1)",
            md,
            flags=re.IGNORECASE
        )

        # Код
        md = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<pre[^>]*>(.*?)</pre>", r"```\n\1\n```", md, flags=re.IGNORECASE | re.DOTALL)

        # Списки
        md = re.sub(r"<ul[^>]*>", "", md, flags=re.IGNORECASE)
        md = re.sub(r"</ul>", "", md, flags=re.IGNORECASE)
        md = re.sub(r"<li[^>]*>", "- ", md, flags=re.IGNORECASE)
        md = re.sub(r"</li>", "\n", md, flags=re.IGNORECASE)

        # Параграфы
        md = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", md, flags=re.IGNORECASE | re.DOTALL)

        # Переносы строк
        md = re.sub(r"<br[^>]*/?>", "\n", md, flags=re.IGNORECASE)

        # Горизонтальная линия
        md = re.sub(r"<hr[^>]*/?>", "\n---\n", md, flags=re.IGNORECASE)

        # Удаление остальных тегов
        md = re.sub(r"<[^>]+>", "", md)

        # Очистка
        md = re.sub(r"\n\s*\n\s*\n", "\n\n", md)

        return md.strip()

    def extract_table(
        self,
        file_path: str,
        table_index: int = 0,
        encoding: str = "utf-8",
    ) -> List[Dict[str, str]]:
        """
        Извлечение таблицы из HTML.

        Args:
            file_path: Путь к файлу.
            table_index: Индекс таблицы.
            encoding: Кодировка.

        Returns:
            Список словарей.
        """
        content = self._read_file(file_path, encoding)

        # Поиск таблиц
        table_pattern = r"<table[^>]*>(.*?)</table>"
        tables = re.findall(table_pattern, content, re.IGNORECASE | re.DOTALL)

        if table_index >= len(tables):
            return []

        table_html = tables[table_index]

        # Поиск строк
        row_pattern = r"<tr[^>]*>(.*?)</tr>"
        rows = re.findall(row_pattern, table_html, re.IGNORECASE | re.DOTALL)

        if not rows:
            return []

        # Первая строка - заголовок
        headers = self._extract_cells(rows[0], "th")

        if not headers:
            headers = self._extract_cells(rows[0], "td")

        result = []

        for row in rows[1:]:
            cells = self._extract_cells(row, "td")

            if not cells:
                cells = self._extract_cells(row, "th")

            row_dict = {}

            for i, cell in enumerate(cells):
                if i < len(headers):
                    row_dict[headers[i]] = cell
                else:
                    row_dict[f"column_{i}"] = cell

            if row_dict:
                result.append(row_dict)

        return result

    def _extract_cells(self, row_html: str, cell_tag: str) -> List[str]:
        """Извлечение ячеек из строки таблицы."""
        pattern = f"<{cell_tag}[^>]*>(.*?)</{cell_tag}>"
        cells = re.findall(pattern, row_html, re.IGNORECASE | re.DOTALL)

        # Очистка от HTML тегов
        return [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells]

    def get_structure(
        self,
        file_path: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        Получение структуры HTML документа.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.

        Returns:
            Структура документа.
        """
        content = self._read_file(file_path, encoding)

        result = {
            "title": self._extract_title(content),
            "meta": self._extract_meta(content),
            "links_count": len(re.findall(r"<a[^>]*href", content, re.IGNORECASE)),
            "images_count": len(re.findall(r"<img[^>]*", content, re.IGNORECASE)),
            "tables_count": len(re.findall(r"<table", content, re.IGNORECASE)),
            "forms_count": len(re.findall(r"<form", content, re.IGNORECASE)),
        }

        return result

    def _extract_title(self, content: str) -> str:
        """Извлечение заголовка страницы."""
        match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_meta(self, content: str) -> Dict[str, str]:
        """Извлечение meta тегов."""
        meta_tags = {}
        pattern = r'<meta[^>]*name="([^"]*)"[^>]*content="([^"]*)"[^>]*/?>'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            meta_tags[match.group(1)] = match.group(2)

        return meta_tags
