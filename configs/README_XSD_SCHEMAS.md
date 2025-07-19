# XSD Schema Validation for VisionAI-ClipsMaster

This directory contains XML Schema Definition (XSD) files used for validating the XML files exported by the VisionAI-ClipsMaster project.

## Available Schemas

- `jianying_v1.xsd`: Schema for Jianying (剪映) video editor XML format
- `premiere_v1.xsd`: Schema for Adobe Premiere Pro XML format

Additional schemas can be added as needed for other formats (FCPXML, DaVinci Resolve, etc.).

## Purpose

These schemas enforce the structure and content requirements for XML files exported by the system, ensuring:

1. Required elements and attributes are present
2. Element types and formats are correct
3. Element relationships follow expected patterns
4. Exported files conform to third-party application expectations

## Usage

The schemas are automatically used by the XML validation system in the codebase. The primary interfaces are:

### Direct Schema Validation

```python
from src.validation.xsd_schema_loader import (
    load_xsd_schema,
    validate_xml_with_schema,
    detect_format_and_version
)

# Detect format and version from XML
format_info = detect_format_and_version('path/to/your.xml')
format_type = format_info["format_type"]  # e.g., "jianying", "premiere"
version = format_info["version"]          # e.g., "1"

# Validate XML against schema
result = validate_xml_with_schema('path/to/your.xml', format_type, version)

if result["valid"]:
    print("XML validation passed!")
else:
    print("XML validation failed:")
    for error in result["errors"]:
        print(f"- {error}")
```

### Integration with XML Validator

```python
from src.export.xml_validator import validate_xml

# Full XML validation (including XSD schema validation)
is_valid = validate_xml('path/to/your.xml', auto_fix=True)
```

Or use the more detailed function:

```python
from src.export.xml_validator import validate_export_xml, validate_schema

# Just schema validation
schema_valid = validate_schema('path/to/your.xml')

# Full validation with details
results = validate_export_xml('path/to/your.xml', strict=True)
print(f"Schema validation: {'PASS' if results['schema'] else 'FAIL'}")
```

## Testing

You can test the schema validation with the provided examples:

```bash
# Create and validate test XML files
python src/examples/simple_xsd_test.py --create both --validate

# Test validation against invalid XML files
python src/examples/invalid_test.py
```

## Extending

To add support for a new XML format:

1. Create a new schema file in this directory (e.g., `new_format_v1.xsd`)
2. Update the detection logic in `detect_format_and_version()` function
3. Add the new format to `SCHEMA_FORMATS` in the `xsd_schema_loader.py` file

## Schema Versioning

Each schema is versioned (e.g., `jianying_v1.xsd`). When updating a schema for a new application version:

1. Create a new file with an incremented version number
2. Keep backward compatibility where possible
3. Update detection logic to recognize version differences

## Schema Implementation Notes

The schemas follow these design principles:

- Required elements and attributes are marked with `use="required"` or `minOccurs="1"`
- Optional elements use `minOccurs="0"` or default values
- Enumerated values are used where appropriate to restrict field values
- Extension points are provided using `xs:any` elements where formats might be extended 