# Universal File Parser

Универсальный инструмент для парсинга, конвертации и анализа различных типов файлов.

## Статус

![Tests](https://img.shields.io/badge/tests-147%20passed-green)
![Python](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## Возможности

### Поддерживаемые форматы (17)

| Категория | Форматы |
|-----------|---------|
| Текстовые | `.txt`, `.md`, `.csv`, `.tsv`, `.log` |
| Табличные | `.xlsx`, `.ods` |
| Данные | `.json`, `.geojson`, `.yaml`, `.yml`, `.toml`, `.ini` |
| Веб | `.xml`, `.html` |
| Бинарные | `.bin` (hex-view) |
| Архивы | `.zip`, `.tar`, `.gz`, `.tgz` |

### Функции

- **Парсинг** — чтение и вывод структуры файлов в удобном формате
- **Конвертация** — CSV ↔ Excel, JSON ↔ YAML, HTML ↔ Markdown
- **Фильтрация** — по ключам, полям, регулярным выражениям, диапазону строк
- **Пакетная обработка** — работа с несколькими файлами одновременно
- **Автоопределение формата** — по расширению и содержимому
- **Поддержка кодировок** — UTF-8, UTF-16, Windows-1251
- **Логирование** — статистика операций

## Установка

```bash
# Установка из исходников
pip install -e .

# Или через pip
pip install universal-file-parser
```

## Использование

### CLI

#### Парсинг файла

```bash
# Парсинг CSV в JSON
parser parse --file data.csv --output data.json

# Парсинг с выводом в консоль
parser parse --file config.yaml

# Пакетная обработка
parser parse --files *.json --output-dir parsed/
```

#### Конвертация

```bash
# JSON в YAML
parser convert --from json --to yaml --file config.json --output config.yaml

# CSV в Excel
parser convert --from csv --to xlsx --file data.csv --output data.xlsx

# HTML в Markdown
parser convert --from html --to md --file page.html --output page.md
```

#### Анализ

```bash
# Анализ лог-файла с фильтрацией
parser analyze --file log.txt --filter "ERROR"

# Анализ с диапазоном строк
parser analyze --file data.csv --start 10 --end 100

# Анализ с регулярным выражением
parser analyze --file app.log --regex "Exception.*"
```

### Python API

```python
from parser import FileParser
from parser.formats import CsvParser, JsonParser

# Использование абстрактного парсера
parser = FileParser()

# Автоматическое определение формата
data = parser.parse("data.csv")
print(data)

# Конвертация
parser.convert("config.json", "yaml", "config.yaml")

# Использование конкретных парсеров
csv_parser = CsvParser()
data = csv_parser.parse("data.csv")

json_parser = JsonParser()
json_data = json_parser.parse("data.json")
```

#### Фильтрация данных

```python
from parser import FileParser

parser = FileParser()

# Фильтрация по ключу
data = parser.parse("data.json", filter_keys=["name", "age"])

# Фильтрация по регулярному выражению
data = parser.parse("log.txt", regex=r"ERROR.*")

# Фильтрация по диапазону строк
data = parser.parse("data.csv", start_line=10, end_line=100)
```

#### Пакетная обработка

```python
from parser import FileParser

parser = FileParser()

# Обработка нескольких файлов
results = parser.parse_batch(["file1.json", "file2.json", "file3.json"])

# Сохранение результатов
for filename, data in results.items():
    parser.save(data, f"output/{filename}")
```

## Структура проекта

```
universal-file-parser/
├── parser/
│   ├── __init__.py
│   ├── cli.py
│   ├── base.py
│   ├── utils.py
│   └── formats/
│       ├── __init__.py
│       ├── text_parser.py
│       ├── csv_parser.py
│       ├── json_parser.py
│       ├── yaml_parser.py
│       ├── xml_parser.py
│       ├── html_parser.py
│       ├── xlsx_parser.py
│       ├── ods_parser.py
│       ├── toml_parser.py
│       ├── ini_parser.py
│       ├── bin_parser.py
│       └── archive_parser.py
├── tests/
│   ├── __init__.py
│   ├── test_csv.py
│   ├── test_json.py
│   ├── test_yaml.py
│   ├── test_xml.py
│   └── test_utils.py
├── README.md
├── requirements.txt
├── setup.py
└── LICENSE
```

## Расширение (плагины)

Для добавления поддержки нового формата создайте класс, наследующий `BaseParser`:

```python
from parser.base import BaseParser

class MyFormatParser(BaseParser):
    extensions = [".myformat"]
    
    def parse(self, file_path: str, encoding: str = "utf-8") -> dict:
        # Реализация парсинга
        pass
    
    def save(self, data: dict, file_path: str) -> None:
        # Реализация сохранения
        pass
```

Зарегистрируйте парсер в `parser/formats/__init__.py`.

## Тесты

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=parser

# Запуск конкретного теста
pytest tests/test_json.py
```

## Лицензия

MIT License

## Вклад в проект

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request
