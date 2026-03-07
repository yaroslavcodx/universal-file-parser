"""
Парсер XML формата.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
from io import StringIO

from parser.base import BaseParser


class XmlParser(BaseParser):
    """Парсер XML файлов."""

    extensions = [".xml"]
    format_name = "xml"

    def parse(
        self,
        file_path: str,
        encoding: str = "utf-8",
        as_dict: bool = True,
        include_attributes: bool = True,
        **kwargs
    ) -> Union[Dict[str, Any], ET.Element]:
        """
        Парсинг XML файла.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            as_dict: Вернуть как словарь.
            include_attributes: Включать атрибуты.

        Returns:
            Распарсенные данные.
        """
        content = self._read_file(file_path, encoding)
        root = ET.fromstring(content)

        if as_dict:
            return self._element_to_dict(root, include_attributes)

        return root

    def _element_to_dict(
        self,
        element: ET.Element,
        include_attributes: bool = True
    ) -> Dict[str, Any]:
        """
        Конвертация XML элемента в словарь.

        Args:
            element: XML элемент.
            include_attributes: Включать атрибуты.

        Returns:
            Словарь.
        """
        result = {}

        # Добавляем атрибуты
        if include_attributes and element.attrib:
            result["@attributes"] = element.attrib

        # Добавляем текст
        text = (element.text or "").strip()
        if text:
            result["#text"] = text

        # Добавляем дочерние элементы
        children = {}

        for child in element:
            child_data = self._element_to_dict(child, include_attributes)

            if child.tag in children:
                # Если элемент уже существует, превращаем в список
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_data)
            else:
                children[child.tag] = child_data

        result.update(children)

        return result

    def save(
        self,
        data: Union[Dict[str, Any], ET.Element],
        file_path: str,
        encoding: str = "utf-8",
        xml_declaration: bool = True,
        indent: str = "  ",
        **kwargs
    ) -> None:
        """
        Сохранение XML файла.

        Args:
            data: Данные.
            file_path: Путь к файлу.
            encoding: Кодировка.
            xml_declaration: Добавлять декларацию.
            indent: Отступ.
        """
        if isinstance(data, dict):
            root = self._dict_to_element(data)
        else:
            root = data

        # Сериализация
        if xml_declaration:
            content = ET.tostring(root, encoding="unicode")
            content = f'<?xml version="1.0" encoding="{encoding}"?>\n{content}'
        else:
            content = ET.tostring(root, encoding="unicode")

        self._write_file(file_path, content, encoding)

    def _dict_to_element(
        self,
        data: Dict[str, Any],
        tag: str = "root"
    ) -> ET.Element:
        """
        Конвертация словаря в XML элемент.

        Args:
            data: Словарь.
            tag: Тег корневого элемента.

        Returns:
            XML элемент.
        """
        element = ET.Element(tag)

        for key, value in data.items():
            if key == "@attributes":
                for attr_name, attr_value in value.items():
                    element.set(attr_name, str(attr_value))
            elif key == "#text":
                element.text = str(value)
            elif isinstance(value, list):
                for item in value:
                    child = self._dict_to_element(item, tag=key)
                    element.append(child)
            elif isinstance(value, dict):
                child = self._dict_to_element(value, tag=key)
                element.append(child)
            else:
                child = ET.Element(key)
                child.text = str(value)
                element.append(child)

        return element

    def find(
        self,
        file_path: str,
        xpath: str,
        encoding: str = "utf-8",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Поиск элементов по XPath.

        Args:
            file_path: Путь к файлу.
            xpath: XPath выражение.
            encoding: Кодировка.

        Returns:
            Список найденных элементов.
        """
        root = self.parse(file_path, encoding=encoding, as_dict=False)
        elements = root.findall(xpath)

        return [self._element_to_dict(elem) for elem in elements]

    def find_text(
        self,
        file_path: str,
        xpath: str,
        encoding: str = "utf-8",
    ) -> List[str]:
        """
        Поиск текста элементов по XPath.

        Args:
            file_path: Путь к файлу.
            xpath: XPath выражение.
            encoding: Кодировка.

        Returns:
            Список текстов.
        """
        root = self.parse(file_path, encoding=encoding, as_dict=False)
        elements = root.findall(xpath)

        return [elem.text for elem in elements if elem.text]

    def validate(
        self,
        file_path: str,
        encoding: str = "utf-8",
        schema_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Валидация XML.

        Args:
            file_path: Путь к файлу.
            encoding: Кодировка.
            schema_path: Путь к XSD схеме.

        Returns:
            Результат валидации.
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            content = self._read_file(file_path, encoding)
            ET.fromstring(content)

            # Валидация по схеме (если предоставлена)
            if schema_path:
                schema_content = self._read_file(schema_path, encoding)
                schema_root = ET.fromstring(schema_content)

                # Примитивная проверка структуры
                # Для полноценной валидации нужен lxml
                result["warnings"].append(
                    "Полная XSD валидация требует lxml. Выполнена базовая проверка."
                )

        except ET.ParseError as e:
            result["valid"] = False
            result["errors"].append(f"XML parse error: {str(e)}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))

        return result

    def to_dict_list(
        self,
        file_path: str,
        item_xpath: str,
        encoding: str = "utf-8",
    ) -> List[Dict[str, Any]]:
        """
        Конвертация XML в список словарей.

        Args:
            file_path: Путь к файлу.
            item_xpath: XPath для элементов.
            encoding: Кодировка.

        Returns:
            Список словарей.
        """
        root = self.parse(file_path, encoding=encoding, as_dict=False)
        elements = root.findall(item_xpath)

        result = []

        for elem in elements:
            item = {}

            for child in elem:
                item[child.tag] = child.text

            result.append(item)

        return result
