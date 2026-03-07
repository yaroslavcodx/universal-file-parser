"""
Примеры использования Universal File Parser.
"""

import json
from parser import FileParser, detect_format, detect_encoding


def example_basic_parsing():
    """Базовый пример парсинга."""
    parser = FileParser()

    # Парсинг JSON
    data = parser.parse("data/config.json")
    print(f"Config: {data}")

    # Парсинг CSV
    rows = parser.parse("data/users.csv")
    print(f"Users: {rows}")

    # Парсинг YAML
    config = parser.parse("data/settings.yaml")
    print(f"Settings: {config}")


def example_filtering():
    """Пример фильтрации данных."""
    parser = FileParser()

    # Фильтрация по ключам
    data = parser.parse("data/large.json", filter_keys=["id", "name"])

    # Фильтрация по regex
    errors = parser.parse("logs/app.log", regex=r"ERROR|CRITICAL")

    # Фильтрация по диапазону
    subset = parser.parse("data/data.csv", start_line=100, end_line=200)


def example_conversion():
    """Пример конвертации."""
    parser = FileParser()

    # JSON в YAML
    parser.convert("config.json", "yaml", "config.yaml")

    # CSV в Excel
    parser.convert("data.csv", "xlsx", "data.xlsx")

    # HTML в Markdown
    parser.convert("page.html", "markdown", "page.md")


def example_batch_processing():
    """Пример пакетной обработки."""
    parser = FileParser()

    # Обработка нескольких файлов
    files = ["file1.json", "file2.json", "file3.json"]
    results = parser.parse_batch(files, output_dir="output/")

    for file_path, result in results.items():
        if result["success"]:
            print(f"{file_path}: {result['stats']['records_count']} записей")
        else:
            print(f"{file_path}: ошибка - {result['error']}")


def example_analysis():
    """Пример анализа файлов."""
    parser = FileParser()

    # Анализ лог-файла
    result = parser.analyze("logs/app.log", filter_pattern="ERROR")

    print(f"Найдено ошибок: {result.get('filtered_count', 0)}")

    # Статистика
    stats = parser.get_stats()
    print(f"Время парсинга: {stats['parse_time']}")


def example_custom_parser():
    """Пример использования кастомного парсера."""
    from parser.base import BaseParser

    class CustomParser(BaseParser):
        extensions = [".dat"]
        format_name = "custom_dat"

        def parse(self, file_path, encoding="utf-8", **kwargs):
            content = self._read_file(file_path, encoding)
            return {"lines": content.split("\n")}

        def save(self, data, file_path, encoding="utf-8", **kwargs):
            content = "\n".join(data.get("lines", []))
            self._write_file(file_path, content, encoding)

    parser = FileParser()
    parser.register_parser("custom_dat", CustomParser)

    data = parser.parse("data/custom.dat")
    print(f"Custom data: {data}")


def example_format_detection():
    """Пример определения формата."""
    # По расширению
    fmt = detect_format("config.json")
    print(f"Format: {fmt}")  # json

    # По содержимому
    encoding = detect_encoding("data/text.txt")
    print(f"Encoding: {encoding}")  # utf-8 или windows-1251


def example_working_with_archives():
    """Пример работы с архивами."""
    parser = FileParser()

    # Список файлов в архиве
    contents = parser.parse("archive.zip", list_only=True)
    print(f"Files in archive: {contents}")

    # Распаковка
    parser.parse("archive.tar.gz", extract_path="extracted/")


def example_hex_dump():
    """Пример hex-дампа бинарного файла."""
    from parser.formats import BinParser

    parser = BinParser()
    result = parser.parse("data/file.bin", hex_view=True)

    print(result["hex_dump"])


def example_xml_processing():
    """Пример обработки XML."""
    from parser.formats import XmlParser

    parser = XmlParser()

    # Поиск по XPath
    items = parser.find("data/catalog.xml", ".//product")

    # Извлечение текста
    names = parser.find_text("data/catalog.xml", ".//product/name")


def example_html_to_markdown():
    """Пример конвертации HTML в Markdown."""
    from parser.formats import HtmlParser

    parser = HtmlParser()

    # Конвертация
    markdown = parser.to_markdown("page.html", "page.md")
    print(markdown)

    # Извлечение структуры
    structure = parser.get_structure("page.html")
    print(f"Title: {structure['title']}")
    print(f"Links: {structure['links_count']}")


def example_excel_processing():
    """Пример обработки Excel файлов."""
    from parser.formats import XlsxParser

    parser = XlsxParser()

    # Парсинг конкретного листа
    data = parser.parse("report.xlsx", sheet="Sales")

    # Информация о файле
    info = parser.get_info("report.xlsx")
    print(f"Sheets: {info['total_sheets']}")

    # Конвертация в CSV
    parser.to_csv("report.xlsx", "report.csv")


def example_ini_processing():
    """Пример обработки INI файлов."""
    from parser.formats import IniParser

    parser = IniParser()

    # Чтение секции
    db_config = parser.get_section("config.ini", "database")

    # Чтение значения
    host = parser.get_value("config.ini", "database", "host")

    # Валидация
    result = parser.validate(
        "config.ini",
        required_sections=["database", "server"],
        required_keys={"database": ["host", "port"]}
    )


if __name__ == "__main__":
    # Запуск примеров
    print("=== Basic Parsing ===")
    # example_basic_parsing()

    print("=== Filtering ===")
    # example_filtering()

    print("=== Conversion ===")
    # example_conversion()

    print("=== Format Detection ===")
    # example_format_detection()

    print("Examples ready to run!")
