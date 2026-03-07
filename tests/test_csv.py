"""
Тесты для CSV парсера.
"""

import pytest
import tempfile
from pathlib import Path

from parser.formats.csv_parser import CsvParser, TsvParser


class TestCsvParser:
    """Тесты для CsvParser."""

    @pytest.fixture
    def parser(self):
        return CsvParser()

    @pytest.fixture
    def csv_file(self, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA")
        return str(file_path)

    def test_parse_basic(self, parser, csv_file):
        data = parser.parse(csv_file)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == 30
        assert data[1]["name"] == "Bob"

    def test_parse_without_header(self, parser, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("Alice,30,NYC\nBob,25,LA")

        data = parser.parse(str(file_path), has_header=False)

        assert isinstance(data, list)
        assert len(data) == 2
        # Без заголовка возвращается список списков
        assert data[0][0] == "Alice"

    def test_parse_type_conversion(self, parser, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("name,active,count\nAlice,true,10\nBob,false,0")

        data = parser.parse(str(file_path))

        assert data[0]["active"] is True
        assert data[0]["count"] == 10
        assert data[1]["active"] is False
        assert data[1]["count"] == 0

    def test_parse_empty_file(self, parser, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("")

        data = parser.parse(str(file_path))

        assert data == []

    def test_save_list_of_dicts(self, parser, tmp_path):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        output_path = tmp_path / "output.csv"

        parser.save(data, str(output_path))

        content = output_path.read_text()
        assert "name,age" in content
        assert "Alice,30" in content
        assert "Bob,25" in content

    def test_save_list_of_lists(self, parser, tmp_path):
        data = [
            ["Alice", 30],
            ["Bob", 25],
        ]
        output_path = tmp_path / "output.csv"

        parser.save(data, str(output_path))

        content = output_path.read_text()
        assert "Alice,30" in content

    def test_save_empty_data(self, parser, tmp_path):
        output_path = tmp_path / "output.csv"

        parser.save([], str(output_path))

        assert output_path.read_text() == ""

    def test_custom_delimiter(self, parser, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("name;age;city\nAlice;30;NYC")

        data = parser.parse(str(file_path), delimiter=";")

        assert data[0]["name"] == "Alice"

    def test_skip_empty_rows(self, parser, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("name,age\n\nAlice,30\n\n")

        data = parser.parse(str(file_path), skip_empty=True)

        assert len(data) == 1

    def test_supports_extension(self):
        assert CsvParser.supports_extension(".csv")
        assert CsvParser.supports_extension("csv")
        assert not CsvParser.supports_extension(".json")

    def test_get_extensions(self):
        extensions = CsvParser.get_extensions()
        assert ".csv" in extensions


class TestTsvParser:
    """Тесты для TsvParser."""

    @pytest.fixture
    def parser(self):
        return TsvParser()

    def test_parse_tsv(self, parser, tmp_path):
        file_path = tmp_path / "test.tsv"
        file_path.write_text("name\tage\tcity\nAlice\t30\tNYC")

        data = parser.parse(str(file_path))

        assert len(data) == 1
        assert data[0]["name"] == "Alice"

    def test_save_tsv(self, parser, tmp_path):
        data = [{"name": "Alice", "age": 30}]
        output_path = tmp_path / "output.tsv"

        parser.save(data, str(output_path))

        content = output_path.read_text()
        assert "\t" in content

    def test_supports_extension(self):
        assert TsvParser.supports_extension(".tsv")
        assert not TsvParser.supports_extension(".csv")
