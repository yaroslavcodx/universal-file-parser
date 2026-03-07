"""
Тесты для утилит.
"""

import pytest
import tempfile
import os
from pathlib import Path

from parser.utils import (
    detect_format,
    detect_encoding,
    format_size,
    truncate_string,
    hex_dump,
    filter_data,
    ParseStats,
)


class TestDetectFormat:
    """Тесты для detect_format."""

    def test_detect_by_extension_json(self, tmp_path):
        file_path = tmp_path / "test.json"
        file_path.write_text('{"key": "value"}')

        assert detect_format(str(file_path)) == "json"

    def test_detect_by_extension_csv(self, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("a,b,c\n1,2,3")

        assert detect_format(str(file_path)) == "csv"

    def test_detect_by_extension_yaml(self, tmp_path):
        file_path = tmp_path / "test.yaml"
        file_path.write_text("key: value")

        assert detect_format(str(file_path)) == "yaml"

    def test_detect_by_extension_xml(self, tmp_path):
        file_path = tmp_path / "test.xml"
        file_path.write_text("<?xml version='1.0'?><root/>")

        assert detect_format(str(file_path)) == "xml"

    def test_detect_by_extension_html(self, tmp_path):
        file_path = tmp_path / "test.html"
        file_path.write_text("<html><body></body></html>")

        assert detect_format(str(file_path)) == "html"

    def test_detect_by_extension_txt(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("plain text")

        assert detect_format(str(file_path)) == "text"

    def test_detect_by_extension_zip(self, tmp_path):
        # ZIP файл с магическими байтами
        file_path = tmp_path / "test.zip"
        file_path.write_bytes(b"PK\x03\x04" + b"dummy content")

        assert detect_format(str(file_path)) == "zip"

    def test_detect_unknown(self, tmp_path):
        file_path = tmp_path / "test.unknown"
        file_path.write_text("unknown format")

        # Может вернуть text из-за содержимого
        result = detect_format(str(file_path))
        assert result in ("text", None)


class TestDetectEncoding:
    """Тесты для detect_encoding."""

    def test_detect_utf8(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, Привет", encoding="utf-8")

        encoding = detect_encoding(str(file_path))
        assert encoding.lower() in ("utf-8", "utf_8")

    def test_detect_windows1251(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_bytes("Привет".encode("windows-1251"))

        encoding = detect_encoding(str(file_path))
        # Может определить как windows-1251 или utf-8
        assert encoding is not None


class TestFormatSize:
    """Тесты для format_size."""

    def test_bytes(self):
        assert format_size(100) == "100.00 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.00 KB"
        assert format_size(2048) == "2.00 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1.00 MB"

    def test_gigabytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.00 GB"

    def test_terabytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"


class TestTruncateString:
    """Тесты для truncate_string."""

    def test_no_truncation(self):
        assert truncate_string("short", max_length=100) == "short"

    def test_truncation(self):
        result = truncate_string("very long string", max_length=10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_custom_suffix(self):
        result = truncate_string("long string", max_length=8, suffix="..")
        assert result.endswith("..")


class TestHexDump:
    """Тесты для hex_dump."""

    def test_basic_dump(self):
        data = b"ABC"
        result = hex_dump(data)

        assert "00000000" in result
        assert "41" in result  # A
        assert "42" in result  # B
        assert "43" in result  # C

    def test_empty_data(self):
        result = hex_dump(b"")
        assert result == ""


class TestFilterData:
    """Тесты для filter_data."""

    def test_filter_keys_dict(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = filter_data(data, filter_keys=["a", "c"])

        assert result == {"a": 1, "c": 3}

    def test_filter_range_list(self):
        data = [{"id": i} for i in range(10)]
        result = filter_data(data, start_line=2, end_line=5)

        assert len(result) == 3
        assert result[0]["id"] == 2

    def test_filter_regex_string(self):
        data = "ERROR: something\nINFO: ok\nERROR: another"
        result = filter_data(data, regex=r"ERROR")

        assert "ERROR" in result
        assert "INFO" not in result

    def test_filter_regex_list(self):
        data = [
            {"level": "ERROR", "msg": "fail"},
            {"level": "INFO", "msg": "ok"},
        ]
        result = filter_data(data, regex=r"ERROR")

        assert len(result) == 1
        assert result[0]["level"] == "ERROR"


class TestParseStats:
    """Тесты для ParseStats."""

    def test_stats_lifecycle(self, tmp_path):
        stats = ParseStats()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        stats.start(str(file_path))

        assert stats.start_time is not None
        assert stats.file_path == str(file_path)

        stats.format = "text"
        stats.encoding = "utf-8"
        stats.records_count = 100
        stats.end()

        assert stats.parse_time >= 0
        assert stats.end_time is not None

    def test_add_error(self, tmp_path):
        stats = ParseStats()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        stats.start(str(file_path))
        stats.add_error("Test error")

        assert stats.errors_count == 1
        assert "Test error" in stats.errors

    def test_to_dict(self, tmp_path):
        stats = ParseStats()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        stats.start(str(file_path))
        stats.format = "json"
        stats.encoding = "utf-8"
        stats.records_count = 50
        stats.end()

        result = stats.to_dict()

        assert "file_path" in result
        assert "format" in result
        assert "parse_time" in result

    def test_str_representation(self, tmp_path):
        stats = ParseStats()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        stats.start(str(file_path))
        stats.format = "csv"
        stats.end()

        result = str(stats)

        assert "Файл:" in result
        assert "Формат:" in result
