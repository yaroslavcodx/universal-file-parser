"""
Тесты для YAML парсера.
"""

import pytest
import yaml
from pathlib import Path

from parser.formats.yaml_parser import YamlParser


class TestYamlParser:
    """Тесты для YamlParser."""

    @pytest.fixture
    def parser(self):
        return YamlParser()

    @pytest.fixture
    def yaml_file(self, tmp_path):
        file_path = tmp_path / "test.yaml"
        data = {"name": "Alice", "age": 30, "city": "NYC"}
        file_path.write_text(yaml.dump(data, allow_unicode=True))
        return str(file_path)

    def test_parse_basic(self, parser, yaml_file):
        data = parser.parse(yaml_file)

        assert isinstance(data, dict)
        assert data["name"] == "Alice"
        assert data["age"] == 30

    def test_parse_list(self, parser, tmp_path):
        file_path = tmp_path / "test.yaml"
        data = [{"id": 1}, {"id": 2}]
        file_path.write_text(yaml.dump(data))

        result = parser.parse(str(file_path))

        assert isinstance(result, list)
        assert len(result) == 2

    def test_parse_nested(self, parser, tmp_path):
        file_path = tmp_path / "test.yaml"
        data = {
            "user": {
                "name": "Alice",
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                }
            }
        }
        file_path.write_text(yaml.dump(data))

        result = parser.parse(str(file_path))

        assert result["user"]["address"]["city"] == "NYC"

    def test_parse_empty_file(self, parser, tmp_path):
        file_path = tmp_path / "test.yaml"
        file_path.write_text("")

        result = parser.parse(str(file_path))

        assert result == {}

    def test_safe_load(self, parser, tmp_path):
        file_path = tmp_path / "test.yaml"
        # Потенциально опасный YAML
        file_path.write_text("!!python/object/apply:os.system ['echo test']")

        # С safe_load=True должен выбросить ошибку
        with pytest.raises(Exception):
            parser.parse(str(file_path), safe_load=True)

    def test_save_dict(self, parser, tmp_path):
        data = {"name": "Bob", "age": 25}
        output_path = tmp_path / "output.yaml"

        parser.save(data, str(output_path))

        content = yaml.safe_load(output_path.read_text())
        assert content["name"] == "Bob"

    def test_save_with_unicode(self, parser, tmp_path):
        data = {"name": "Test", "value": 42}
        output_path = tmp_path / "output.yaml"

        parser.save(data, str(output_path), allow_unicode=True)

        content = output_path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(content)
        assert loaded["name"] == "Test"
        assert loaded["value"] == 42

    def test_validate_valid_yaml(self, parser, yaml_file):
        result = parser.validate(yaml_file)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_yaml(self, parser, tmp_path):
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text("invalid: yaml: content:")

        result = parser.validate(str(file_path))

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_merge_files(self, parser, tmp_path):
        file1 = tmp_path / "file1.yaml"
        file2 = tmp_path / "file2.yaml"

        file1.write_text(yaml.dump({"a": 1, "b": 2}))
        file2.write_text(yaml.dump({"b": 3, "c": 4}))

        result = parser.merge([str(file1), str(file2)], deep_merge=True)

        assert result["a"] == 1
        assert result["b"] == 3  # Переписано вторым файлом
        assert result["c"] == 4

    def test_merge_shallow(self, parser, tmp_path):
        file1 = tmp_path / "file1.yaml"
        file2 = tmp_path / "file2.yaml"

        file1.write_text(yaml.dump({"a": {"x": 1, "y": 2}}))
        file2.write_text(yaml.dump({"a": {"z": 3}}))

        result = parser.merge([str(file1), str(file2)], deep_merge=False)

        # При shallow merge второй файл полностью заменяет первый
        assert "x" not in result["a"]
        assert result["a"]["z"] == 3

    def test_to_json(self, parser, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        json_file = tmp_path / "output.json"

        data = {"name": "Alice", "age": 30}
        yaml_file.write_text(yaml.dump(data))

        parser.to_json(str(yaml_file), str(json_file))

        result = yaml.safe_load(json_file.read_text())
        assert result["name"] == "Alice"

    def test_from_json(self, parser, tmp_path):
        import json
        json_file = tmp_path / "test.json"
        yaml_file = tmp_path / "output.yaml"

        data = {"name": "Bob", "age": 25}
        json_file.write_text(json.dumps(data))

        parser.from_json(str(json_file), str(yaml_file))

        result = yaml.safe_load(yaml_file.read_text())
        assert result["name"] == "Bob"

    def test_supports_extension(self):
        assert YamlParser.supports_extension(".yaml")
        assert YamlParser.supports_extension(".yml")
        assert YamlParser.supports_extension("yaml")
        assert not YamlParser.supports_extension(".json")
