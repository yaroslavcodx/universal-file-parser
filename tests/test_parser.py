"""
Тесты для основного FileParser.
"""

import pytest
import json
from pathlib import Path

from parser.parser import FileParser
from parser.base import BaseParser


class TestFileParser:
    """Тесты для FileParser."""

    @pytest.fixture
    def parser(self):
        return FileParser()

    @pytest.fixture
    def json_file(self, tmp_path):
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps({"name": "Alice", "age": 30}))
        return str(file_path)

    @pytest.fixture
    def csv_file(self, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("name,age\nAlice,30\nBob,25")
        return str(file_path)

    def test_parse_json(self, parser, json_file):
        data = parser.parse(json_file)

        assert isinstance(data, dict)
        assert data["name"] == "Alice"

    def test_parse_csv(self, parser, csv_file):
        data = parser.parse(csv_file)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_parse_with_encoding(self, parser, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("Привет мир", encoding="utf-8")

        data = parser.parse(str(file_path), encoding="utf-8")

        assert "Привет" in data

    def test_parse_with_filter_keys(self, parser, json_file):
        data = parser.parse(json_file, filter_keys=["name"])

        assert "name" in data
        assert "age" not in data

    def test_parse_with_regex(self, parser, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("ERROR: fail\nINFO: ok\nERROR: another fail")

        data = parser.parse(str(file_path), regex=r"ERROR")

        assert "ERROR" in data
        assert "INFO" not in data

    def test_parse_with_range(self, parser, csv_file):
        data = parser.parse(csv_file, start_line=0, end_line=1)

        assert len(data) == 1

    def test_parse_unknown_format(self, parser, tmp_path):
        file_path = tmp_path / "test.unknown"
        file_path.write_text("unknown content")

        with pytest.raises(ValueError):
            parser.parse(str(file_path))

    def test_parse_batch(self, parser, tmp_path):
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        file1.write_text(json.dumps({"id": 1}))
        file2.write_text(json.dumps({"id": 2}))

        results = parser.parse_batch([str(file1), str(file2)])

        assert str(file1) in results
        assert str(file2) in results
        assert results[str(file1)]["success"] is True
        assert results[str(file2)]["success"] is True

    def test_parse_batch_with_output(self, parser, tmp_path):
        file1 = tmp_path / "file1.json"
        output_dir = tmp_path / "output"

        file1.write_text(json.dumps({"id": 1}))

        results = parser.parse_batch([str(file1)], output_dir=str(output_dir))

        assert (output_dir / "file1.json").exists()

    def test_save_json(self, parser, tmp_path):
        data = {"name": "Bob", "age": 25}
        output_path = tmp_path / "output.json"

        parser.save(data, str(output_path))

        result = json.loads(output_path.read_text())
        assert result["name"] == "Bob"

    def test_save_with_format(self, parser, tmp_path):
        data = [{"name": "Alice"}]
        output_path = tmp_path / "output.csv"

        parser.save(data, str(output_path), format_name="csv")

        content = output_path.read_text()
        assert "name" in content
        assert "Alice" in content

    def test_convert_json_to_yaml(self, parser, tmp_path):
        json_file = tmp_path / "test.json"
        yaml_file = tmp_path / "output.yaml"

        json_file.write_text(json.dumps({"name": "Alice", "age": 30}))

        result_path = parser.convert(str(json_file), "yaml", str(yaml_file))

        assert result_path == str(yaml_file)
        assert yaml_file.exists()

    def test_analyze(self, parser, json_file):
        result = parser.analyze(json_file)

        assert "file" in result
        assert "format" in result
        assert "records" in result
        assert result["format"] == "json"

    def test_analyze_with_filter(self, parser, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("ERROR: fail\nINFO: ok\nERROR: another")

        result = parser.analyze(str(file_path), filter_pattern="ERROR")

        assert "filtered_lines" in result
        assert result["filtered_count"] == 2

    def test_get_supported_formats(self, parser):
        formats = parser.get_supported_formats()

        assert "json" in formats
        assert "csv" in formats
        assert "yaml" in formats
        assert "xml" in formats

    def test_get_stats(self, parser, json_file):
        parser.parse(json_file)
        stats = parser.get_stats()

        assert stats is not None
        assert "file_path" in stats
        assert "format" in stats

    def test_register_custom_parser(self, parser, tmp_path):
        class CustomParser(BaseParser):
            extensions = [".custom"]
            format_name = "custom"

            def parse(self, file_path, encoding="utf-8", **kwargs):
                return {"custom": self._read_file(file_path, encoding)}

            def save(self, data, file_path, encoding="utf-8", **kwargs):
                self._write_file(file_path, str(data), encoding)

        parser.register_parser("custom", CustomParser)

        file_path = tmp_path / "test.custom"
        file_path.write_text("test content")

        # Указываем формат явно, т.к. .custom не определяется автоматически
        data = parser.parse(str(file_path), format_name="custom")

        assert data["custom"] == "test content"

    def test_last_stats_updated(self, parser, json_file):
        assert parser.last_stats is None

        parser.parse(json_file)

        assert parser.last_stats is not None
        assert parser.last_stats.format == "json"

    def test_parse_geojson(self, parser, tmp_path):
        file_path = tmp_path / "test.geojson"
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "Test"}
                }
            ]
        }
        file_path.write_text(json.dumps(geojson))

        data = parser.parse(str(file_path))

        assert data["type"] == "FeatureCollection"

    def test_parse_error_handling(self, parser, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{invalid json}")

        with pytest.raises(Exception):
            parser.parse(str(file_path))

        # Stats should contain error info
        if parser.last_stats:
            assert parser.last_stats.errors_count > 0
