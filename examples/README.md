# Примеры данных для тестирования парсера

Эта директория содержит примеры файлов для тестирования парсера.

## Создание тестовых файлов

### JSON
```json
{
    "name": "Test",
    "value": 42
}
```

### CSV
```csv
name,age,city
Alice,30,NYC
Bob,25,LA
```

### YAML
```yaml
database:
  host: localhost
  port: 5432
server:
  port: 8080
```

### XML
```xml
<?xml version="1.0"?>
<catalog>
    <product id="1">
        <name>Product 1</name>
        <price>99.99</price>
    </product>
</catalog>
```

### INI
```ini
[database]
host = localhost
port = 5432

[server]
port = 8080
```
