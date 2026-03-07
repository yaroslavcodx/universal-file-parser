# Вклад в проект

Спасибо за интерес к проекту Universal File Parser! Этот документ содержит рекомендации по внесению вклада.

## Как внести вклад

### 1. Сообщение об ошибке

Если вы нашли ошибку:

1. Проверьте существующие issues
2. Создайте новый issue с описанием:
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Версия Python и ОС

### 2. Предложение функции

Для новых функций:

1. Создайте issue с описанием функциональности
2. Обсудите реализацию с maintainer'ами
3. После одобрения приступайте к реализации

### 3. Pull Request

#### Подготовка

```bash
# Fork репозитория
git clone https://github.com/YOUR_USERNAME/universal-file-parser.git
cd universal-file-parser

# Создайте ветку
git checkout -b feature/amazing-feature
```

#### Требования к коду

- Следуйте PEP 8
- Добавляйте type hints
- Пишите docstrings для публичных функций
- Добавляйте тесты для нового функционала

#### Запуск тестов

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=parser

# Линтинг
flake8 parser/ tests/
```

#### Отправка PR

```bash
git add .
git commit -m "feat: добавить amazing feature"
git push origin feature/amazing-feature
```

Создайте Pull Request на GitHub.

## Соглашения по коммитам

Используем [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` новая функция
- `fix:` исправление ошибки
- `docs:` документация
- `style:` форматирование
- `refactor:` рефакторинг
- `test:` тесты
- `chore:` обслуживание

Пример:
```
feat: добавить поддержку формата PARQUET
fix: исправить ошибку парсинга CSV с пустыми строками
docs: обновить README.md
```

## Структура проекта

```
universal-file-parser/
├── parser/              # Исходный код
│   ├── formats/         # Парсеры форматов
│   ├── base.py          # Базовый класс
│   ├── parser.py        # Основной парсер
│   ├── utils.py         # Утилиты
│   └── cli.py           # CLI интерфейс
├── tests/               # Тесты
├── docs/                # Документация
└── examples/            # Примеры использования
```

## Добавление нового парсера

1. Создайте файл в `parser/formats/`:

```python
from parser.base import BaseParser

class MyFormatParser(BaseParser):
    extensions = [".myformat"]
    format_name = "myformat"

    def parse(self, file_path: str, encoding: str = "utf-8", **kwargs):
        # Реализация
        pass

    def save(self, data, file_path: str, **kwargs):
        # Реализация
        pass
```

2. Добавьте экспорт в `parser/formats/__init__.py`
3. Добавьте парсер в `FORMAT_PARSERS`
4. Напишите тесты
5. Обновите документацию

## Тестирование

### Юнит-тесты

```python
import pytest
from parser.formats import MyFormatParser

class TestMyFormatParser:
    @pytest.fixture
    def parser(self):
        return MyFormatParser()

    def test_parse(self, parser, tmp_path):
        # Тест
        pass
```

### Интеграционные тесты

Тесты взаимодействия между компонентами.

## Документация

- Обновляйте README.md при изменении API
- Добавляйте примеры использования
- Документируйте публичные функции

## Вопросы?

Создайте issue или свяжитесь с maintainer'ами.
