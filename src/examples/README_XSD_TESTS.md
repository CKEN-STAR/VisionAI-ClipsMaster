# XML Schema Validation Tests

This directory contains test scripts for the XSD schema validation system.

## Overview

The XML Schema Definition (XSD) validation system helps ensure that XML files exported by the VisionAI-ClipsMaster project conform to the expected formats. These test scripts demonstrate how to use the validation functionality and test its effectiveness.

## Available Tests

### 1. Simple XSD Test (`simple_xsd_test.py`)

A straightforward demonstration of creating valid XML files and validating them against our XSD schemas.

```bash
# Create and validate both Jianying and Premiere XML files
python src/examples/simple_xsd_test.py --create both --validate

# Create only a Jianying test file
python src/examples/simple_xsd_test.py --create jianying --validate

# Create only a Premiere test file
python src/examples/simple_xsd_test.py --create premiere --validate

# Validate existing files without creating new ones
python src/examples/simple_xsd_test.py --validate
```

### 2. Invalid XML Test (`invalid_test.py`)

Creates intentionally invalid XML files to verify that the XSD validation correctly identifies problems.

```bash
# Test both Jianying and Premiere validation (default)
python src/examples/invalid_test.py

# Test only Jianying validation
python src/examples/invalid_test.py --create jianying

# Test only Premiere validation
python src/examples/invalid_test.py --create premiere
```

## Integration with Core Validation

To use the XSD validation in the main application code:

```python
# Direct validation using the validation module
from src.validation import (
    validate_xml_with_schema,
    detect_format_and_version
)

# Validation through the XML validator
from src.export.xml_validator import (
    validate_schema,
    validate_export_xml
)
```

## Adding New Tests

When adding new XML formats:

1. Create a new schema in the `configs/` directory
2. Add test functions in these scripts or create new scripts
3. Update the formats supported in `src/validation/xsd_schema_loader.py`

## Design Notes

- Test scripts should be independent and runnable without external dependencies
- Each script should clearly indicate success/failure of tests
- Tests should cover both valid and invalid cases
- Implementation should match the real-world usage patterns 