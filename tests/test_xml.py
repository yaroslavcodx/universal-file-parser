"""
Тесты для XML парсера.
"""

import pytest
from pathlib import Path

from parser.formats.xml_parser import XmlParser


class TestXmlParser:
    """Тесты для XmlParser."""

    @pytest.fixture
    def parser(self):
        return XmlParser()

    @pytest.fixture
    def xml_file(self, tmp_path):
        file_path = tmp_path / "test.xml"
        content = """<?xml version="1.0"?>
        <root>
            <item id="1">
                <name>Alice</name>
                <age>30</age>
            </item>
            <item id="2">
                <name>Bob</name>
                <age>25</age>
            </item>
        </root>"""
        file_path.write_text(content)
        return str(file_path)

    def test_parse_basic(self, parser, xml_file):
        data = parser.parse(xml_file)

        assert isinstance(data, dict)
        assert "item" in data

    def test_parse_as_element(self, parser, xml_file):
        data = parser.parse(xml_file, as_dict=False)

        from xml.etree.ElementTree import Element
        assert isinstance(data, Element)
        assert data.tag == "root"

    def test_parse_with_attributes(self, parser, xml_file):
        data = parser.parse(xml_file)

        # Поиск элемента item
        items = data.get("item", [])
        if isinstance(items, dict):
            items = [items]

        assert len(items) == 2
        assert "@attributes" in items[0]
        assert items[0]["@attributes"]["id"] == "1"

    def test_parse_without_attributes(self, parser, xml_file):
        data = parser.parse(xml_file, include_attributes=False)

        # Поиск элемента item
        items = data.get("item", [])
        if isinstance(items, dict):
            items = [items]

        if items:
            assert "@attributes" not in items[0]

    def test_save_dict(self, parser, tmp_path):
        data = {
            "root": {
                "item": {
                    "name": "Alice",
                    "age": "30"
                }
            }
        }
        output_path = tmp_path / "output.xml"

        parser.save(data, str(output_path))

        content = output_path.read_text()
        assert "<root>" in content
        assert "<name>Alice</name>" in content

    def test_save_with_attributes(self, parser, tmp_path):
        data = {
            "root": {
                "@attributes": {"version": "1.0"},
                "item": {"name": "Alice"}
            }
        }
        output_path = tmp_path / "output.xml"

        parser.save(data, str(output_path))

        content = output_path.read_text()
        assert 'version="1.0"' in content

    def test_find_xpath(self, parser, xml_file):
        items = parser.find(xml_file, ".//item")

        assert len(items) == 2

    def test_find_text(self, parser, xml_file):
        names = parser.find_text(xml_file, ".//name")

        assert "Alice" in names
        assert "Bob" in names

    def test_validate_valid_xml(self, parser, xml_file):
        result = parser.validate(xml_file)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_xml(self, parser, tmp_path):
        file_path = tmp_path / "invalid.xml"
        file_path.write_text("<root><unclosed>")

        result = parser.validate(str(file_path))

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_to_dict_list(self, parser, xml_file):
        items = parser.to_dict_list(xml_file, ".//item")

        assert len(items) == 2
        assert items[0].get("name") == "Alice"

    def test_element_to_dict_nested(self, parser, tmp_path):
        file_path = tmp_path / "test.xml"
        content = """<?xml version="1.0"?>
        <root>
            <user>
                <name>Alice</name>
                <address>
                    <city>NYC</city>
                </address>
            </user>
        </root>"""
        file_path.write_text(content)

        data = parser.parse(str(file_path))

        assert "user" in data
        assert "address" in data["user"]

    def test_multiple_same_elements(self, parser, tmp_path):
        file_path = tmp_path / "test.xml"
        content = """<?xml version="1.0"?>
        <root>
            <item>1</item>
            <item>2</item>
            <item>3</item>
        </root>"""
        file_path.write_text(content)

        data = parser.parse(str(file_path))

        # Multiple same elements should be a list
        assert isinstance(data["item"], list)
        assert len(data["item"]) == 3

    def test_supports_extension(self):
        assert XmlParser.supports_extension(".xml")
        assert XmlParser.supports_extension("xml")
        assert not XmlParser.supports_extension(".html")

    def test_get_info(self, parser):
        info = parser.get_info()

        assert info["format_name"] == "xml"
        assert ".xml" in info["extensions"]
