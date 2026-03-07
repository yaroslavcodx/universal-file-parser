"""
Тесты для JSON парсера.
"""

import pytest
import json
from pathlib import Path

from parser.formats.json_parser import JsonParser


class TestJsonParser:
    """Тесты для JsonParser."""

    @pytest.fixture
    def parser(self):
        return JsonParser()

    @pytest.fixture
    def json_file(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"name": "Alice", "age": 30, "city": "NYC"}
        file_path.write_text(json.dumps(data, ensure_ascii=False))
        return str(file_path)

    def test_parse_basic(self, parser, json_file):
        data = parser.parse(json_file)

        assert isinstance(data, dict)
        assert data["name"] == "Alice"
        assert data["age"] == 30

    def test_parse_list(self, parser, tmp_path):
        file_path = tmp_path / "test.json"
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        file_path.write_text(json.dumps(data))

        result = parser.parse(str(file_path))

        assert isinstance(result, list)
        assert len(result) == 3

    def test_parse_nested(self, parser, tmp_path):
        file_path = tmp_path / "test.json"
        data = {
            "user": {
                "name": "Alice",
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                }
            }
        }
        file_path.write_text(json.dumps(data))

        result = parser.parse(str(file_path))

        assert result["user"]["address"]["city"] == "NYC"

    def test_parse_flatten(self, parser, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"user": {"name": "Alice", "age": 30}}
        file_path.write_text(json.dumps(data))

        result = parser.parse(str(file_path), flatten=True)

        assert "user.name" in result
        assert result["user.name"] == "Alice"

    def test_save_dict(self, parser, tmp_path):
        data = {"name": "Bob", "age": 25}
        output_path = tmp_path / "output.json"

        parser.save(data, str(output_path))

        content = json.loads(output_path.read_text())
        assert content["name"] == "Bob"

    def test_save_with_indent(self, parser, tmp_path):
        data = {"name": "Bob"}
        output_path = tmp_path / "output.json"

        parser.save(data, str(output_path), indent=4)

        content = output_path.read_text()
        assert "    " in content  # 4 spaces indent

    def test_save_with_sort_keys(self, parser, tmp_path):
        data = {"z": 1, "a": 2, "m": 3}
        output_path = tmp_path / "output.json"

        parser.save(data, str(output_path), sort_keys=True)

        content = output_path.read_text()
        # Keys should be in alphabetical order
        assert content.index('"a"') < content.index('"m"') < content.index('"z"')

    def test_validate_valid_json(self, parser, json_file):
        result = parser.validate(json_file)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_json(self, parser, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{invalid json}")

        result = parser.validate(str(file_path))

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_with_schema(self, parser, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"name": "Alice", "age": 30}
        file_path.write_text(json.dumps(data))

        schema = {
            "type": "object",
            "required": ["name", "age"]
        }

        result = parser.validate(str(file_path), schema=schema)

        assert result["valid"] is True

    def test_validate_missing_required_field(self, parser, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"name": "Alice"}  # Missing "age"
        file_path.write_text(json.dumps(data))

        schema = {
            "type": "object",
            "required": ["name", "age"]
        }

        result = parser.validate(str(file_path), schema=schema)

        assert result["valid"] is False
        assert any("age" in err for err in result["errors"])

    def test_merge_files(self, parser, tmp_path):
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        file1.write_text(json.dumps([{"id": 1}]))
        file2.write_text(json.dumps([{"id": 2}]))

        result = parser.merge([str(file1), str(file2)])

        assert len(result) == 2

    def test_merge_by_key(self, parser, tmp_path):
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        file1.write_text(json.dumps([{"id": 1, "name": "Alice"}]))
        file2.write_text(json.dumps([{"id": 1, "age": 30}]))

        result = parser.merge([str(file1), str(file2)], merge_key="id")

        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == 30

    def test_geojson_extension(self):
        assert JsonParser.supports_extension(".geojson")

    def test_get_info(self, parser):
        info = parser.get_info()

        assert info["format_name"] == "json"
        assert ".json" in info["extensions"]
