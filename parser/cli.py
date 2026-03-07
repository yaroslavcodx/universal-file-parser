"""
CLI интерфейс для универсального парсера файлов.
"""

import sys
import json
import glob as glob_module
from pathlib import Path
from typing import Optional, List

import click

from parser import FileParser, detect_format, detect_encoding
from parser.utils import format_size, ParseStats


@click.group()
@click.version_option(version="1.0.0", prog_name="parser")
def main():
    """
    Universal File Parser - Универсальный парсер файлов.

    Поддерживает парсинг, конвертацию и анализ различных типов файлов.
    """
    pass


@main.command()
@click.option("--file", "-f", "file_path", help="Путь к файлу для парсинга")
@click.option("--files", "-F", "files_pattern", help="Шаблон для нескольких файлов (например, *.json)")
@click.option("--output", "-o", "output_path", help="Путь для сохранения результата")
@click.option("--output-dir", "-d", "output_dir", help="Директория для сохранения результатов")
@click.option("--format", "format_name", help="Формат файла (автоопределение если не указан)")
@click.option("--encoding", "-e", default=None, help="Кодировка файла")
@click.option("--filter-keys", "-k", help="Ключи для фильтрации (через запятую)")
@click.option("--regex", "-r", help="Регулярное выражение для фильтрации")
@click.option("--start-line", type=int, help="Начальная строка")
@click.option("--end-line", type=int, help="Конечная строка")
@click.option("--quiet", "-q", is_flag=True, help="Тихий режим (без вывода статистики)")
@click.option("--pretty", "-p", is_flag=True, help="Красивый вывод JSON")
def parse(
    file_path: Optional[str],
    files_pattern: Optional[str],
    output_path: Optional[str],
    output_dir: Optional[str],
    format_name: Optional[str],
    encoding: Optional[str],
    filter_keys: Optional[str],
    regex: Optional[str],
    start_line: Optional[int],
    end_line: Optional[int],
    quiet: bool,
    pretty: bool,
):
    """
    Парсинг файла.

    Примеры:

        parser parse --file data.csv --output data.json

        parser parse --files "*.json" --output-dir parsed/

        parser parse --file config.yaml --filter-keys "database,server"
    """
    parser = FileParser()

    # Определение списка файлов
    files = _get_files(file_path, files_pattern)

    if not files:
        click.echo("Ошибка: Не указаны файлы или файлы не найдены", err=True)
        sys.exit(1)

    # Обработка ключей фильтрации
    filter_keys_list = None

    if filter_keys:
        filter_keys_list = [k.strip() for k in filter_keys.split(",")]

    results = {}

    for fp in files:
        try:
            data = parser.parse(
                fp,
                encoding=encoding,
                format_name=format_name,
                filter_keys=filter_keys_list,
                regex=regex,
                start_line=start_line,
                end_line=end_line,
            )

            results[fp] = data

            # Сохранение
            if output_path and len(files) == 1:
                _save_result(data, output_path, pretty)
            elif output_dir:
                out_file = Path(output_dir) / f"{Path(fp).stem}.json"
                out_file.parent.mkdir(parents=True, exist_ok=True)
                _save_result(data, str(out_file), pretty)

            # Вывод в консоль
            if not output_path and not output_dir:
                if len(files) > 1:
                    click.echo(f"\n=== {fp} ===")

                if isinstance(data, (dict, list)):
                    click.echo(json.dumps(data, indent=2 if pretty else None, ensure_ascii=False))
                else:
                    click.echo(str(data)[:1000])  # Ограничение вывода

            # Статистика
            if not quiet and parser.last_stats:
                _print_stats(parser.last_stats, verbose=len(files) == 1)

        except Exception as e:
            click.echo(f"Ошибка при парсинге {fp}: {str(e)}", err=True)
            results[fp] = {"error": str(e)}

    # Сохранение всех результатов
    if output_path and len(files) > 1:
        _save_result(results, output_path, pretty)


@main.command()
@click.option("--file", "-f", "input_file", required=True, help="Входной файл")
@click.option("--from", "from_format", help="Входной формат")
@click.option("--to", "to_format", required=True, help="Выходной формат")
@click.option("--output", "-o", "output_file", help="Выходной файл")
@click.option("--encoding", "-e", default=None, help="Кодировка")
def convert(
    input_file: str,
    from_format: Optional[str],
    to_format: str,
    output_file: Optional[str],
    encoding: Optional[str],
):
    """
    Конвертация между форматами.

    Примеры:

        parser convert --file config.json --to yaml --output config.yaml

        parser convert --file data.csv --to xlsx --output data.xlsx

        parser convert --file page.html --to md --output page.md
    """
    parser = FileParser()

    try:
        result_file = parser.convert(
            input_file,
            to_format,
            output_file,
            encoding=encoding,
        )

        click.echo(f"Файл сконвертирован: {result_file}")

        if parser.last_stats:
            _print_stats(parser.last_stats)

    except Exception as e:
        click.echo(f"Ошибка конвертации: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.option("--file", "-f", "file_path", required=True, help="Файл для анализа")
@click.option("--filter", "filter_pattern", help="Паттерн для фильтрации строк")
@click.option("--regex", "-r", help="Регулярное выражение")
@click.option("--start-line", type=int, help="Начальная строка")
@click.option("--end-line", type=int, help="Конечная строка")
@click.option("--stats", "-s", is_flag=True, help="Только статистика")
def analyze(
    file_path: str,
    filter_pattern: Optional[str],
    regex: Optional[str],
    start_line: Optional[int],
    end_line: Optional[int],
    stats: bool,
):
    """
    Анализ файла.

    Примеры:

        parser analyze --file log.txt --filter "ERROR"

        parser analyze --file data.csv --stats

        parser analyze --file app.log --regex "Exception.*"
    """
    parser = FileParser()

    try:
        result = parser.analyze(
            file_path,
            filter_pattern=filter_pattern,
            regex=regex,
            start_line=start_line,
            end_line=end_line,
        )

        if stats:
            click.echo("=== Статистика ===")
            click.echo(f"Файл: {result['file']}")
            click.echo(f"Формат: {result['format']}")
            click.echo(f"Кодировка: {result['encoding']}")
            click.echo(f"Размер: {format_size(result['size'])}")
            click.echo(f"Записей: {result['records']}")
            click.echo(f"Время парсинга: {result['parse_time']:.3f}s")
        else:
            click.echo("=== Результаты анализа ===")
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        click.echo(f"Ошибка анализа: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.option("--file", "-f", "file_path", required=True, help="Файл для проверки")
@click.option("--encoding", "-e", is_flag=True, help="Проверить кодировку")
@click.option("--structure", "-s", is_flag=True, help="Показать структуру")
def validate(
    file_path: str,
    encoding: bool,
    structure: bool,
):
    """
    Валидация файла.

    Примеры:

        parser validate --file data.json

        parser validate --file config.yaml --encoding
    """
    parser = FileParser()

    detected_format = detect_format(file_path)
    detected_encoding = detect_encoding(file_path)

    click.echo("=== Информация о файле ===")
    click.echo(f"Путь: {file_path}")
    click.echo(f"Размер: {format_size(Path(file_path).stat().st_size)}")
    click.echo(f"Формат: {detected_format or 'не определен'}")
    click.echo(f"Кодировка: {detected_encoding}")

    if structure:
        try:
            data = parser.parse(file_path)

            if isinstance(data, dict):
                click.echo(f"\nКлючи верхнего уровня: {list(data.keys())}")
            elif isinstance(data, list):
                click.echo(f"\nКоличество записей: {len(data)}")

                if data:
                    click.echo(f"Структура первой записи: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")

        except Exception as e:
            click.echo(f"Ошибка при чтении структуры: {str(e)}", err=True)


@main.command()
def formats():
    """
    Список поддерживаемых форматов.
    """
    parser = FileParser()
    supported = parser.get_supported_formats()

    click.echo("=== Поддерживаемые форматы ===\n")

    for format_name, extensions in sorted(supported.items()):
        click.echo(f"{format_name}: {', '.join(extensions)}")


@main.command()
@click.argument("archive_path")
@click.option("--output", "-o", "output_dir", help="Директория для распаковки")
@click.option("--list", "-l", "list_only", is_flag=True, help="Только список файлов")
def extract(archive_path: str, output_dir: Optional[str], list_only: bool):
    """
    Распаковка архива.

    Примеры:

        parser extract archive.zip

        parser extract archive.zip --output extracted/

        parser extract archive.tar.gz --list
    """
    parser = FileParser()

    try:
        format_name = detect_format(archive_path)

        if format_name not in ("zip", "tar", "gzip"):
            click.echo(f"Ошибка: {archive_path} не является поддерживаемым архивом", err=True)
            sys.exit(1)

        data = parser.parse(archive_path, list_only=list_only, extract_path=output_dir)

        if list_only or not output_dir:
            if isinstance(data, dict):
                click.echo(f"Всего файлов: {data.get('total_files', 0)}")

                for file_info in data.get("files", []):
                    size = file_info.get("size", 0)
                    name = file_info.get("filename") or file_info.get("name")
                    click.echo(f"  {name} ({format_size(size) if size else '0 B'})")
            elif isinstance(data, list):
                for item in data:
                    click.echo(f"  {item}")

        if output_dir:
            click.echo(f"Архив распакован в: {output_dir}")

    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        sys.exit(1)


def _get_files(
    file_path: Optional[str],
    files_pattern: Optional[str],
) -> List[str]:
    """Получение списка файлов."""
    files = []

    if file_path:
        files.append(file_path)

    if files_pattern:
        files.extend(glob_module.glob(files_pattern))

    return files


def _save_result(data, output_path: str, pretty: bool) -> None:
    """Сохранение результата."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, (dict, list)):
        indent = 2 if pretty else None
        content = json.dumps(data, indent=indent, ensure_ascii=False)
    else:
        content = str(data)

    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def _print_stats(stats: ParseStats, verbose: bool = True) -> None:
    """Вывод статистики."""
    if verbose:
        click.echo(f"\n=== Статистика ===")
        click.echo(f"Время парсинга: {stats.parse_time:.3f}s")
        click.echo(f"Записей: {stats.records_count}")
        click.echo(f"Ошибок: {stats.errors_count}")

        if stats.errors:
            click.echo("Ошибки:")
            for error in stats.errors:
                click.echo(f"  - {error}")
    else:
        click.echo(f"  [{stats.records_count} записей, {stats.parse_time:.3f}s]")


if __name__ == "__main__":
    main()
