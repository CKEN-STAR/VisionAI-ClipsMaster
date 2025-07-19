#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XSD Schema Loader Module

This module provides functionality to load XSD schema files for XML validation.
It supports different XML formats and versions used in the project.

Key features:
1. Loading XSD schemas for different formats (Premiere, FCPXML, DaVinci, Jianying)
2. Version-specific schema selection
3. Schema caching for performance
4. Validation helpers
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, Optional, Union, Any
import xml.etree.ElementTree as ET
from lxml import etree
import logging

# Add project root to path to ensure module can be imported from anywhere
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # Simple logging fallback
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# Configure logger
logger = get_logger("xsd_schema_loader")

# Schema format types
SCHEMA_FORMATS = {
    "premiere": "premiere",
    "fcpxml": "fcpxml",
    "davinci": "davinci",
    "jianying": "jianying",
    "default": "premiere"
}

# Schema cache
_schema_cache: Dict[str, Any] = {}


def load_xsd_schema(format_type: str = "default", version: str = "1") -> Optional[etree.XMLSchema]:
    """
    Load the XSD schema for the specified format and version.
    
    Args:
        format_type: The format type ("premiere", "fcpxml", "davinci", "jianying")
        version: Schema version
        
    Returns:
        Optional[etree.XMLSchema]: The loaded schema or None if not found
    """
    # Normalize format type
    format_type = format_type.lower()
    if format_type not in SCHEMA_FORMATS:
        format_type = "default"
        
    # Create cache key
    cache_key = f"{format_type}_{version}"
    
    # Check if schema is in cache
    if cache_key in _schema_cache:
        logger.debug(f"Using cached schema for {format_type} version {version}")
        return _schema_cache[cache_key]
    
    # Build schema path
    schema_base_dir = project_root / "configs"
    schema_filename = f"{format_type}_v{version}.xsd"
    schema_path = schema_base_dir / schema_filename
    
    logger.info(f"Loading XSD schema: {schema_path}")
    
    # Check if schema file exists
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}")
        return None
    
    try:
        # Parse and compile the schema
        xmlschema_doc = etree.parse(str(schema_path))
        schema = etree.XMLSchema(xmlschema_doc)
        
        # Cache the schema
        _schema_cache[cache_key] = schema
        
        logger.info(f"Successfully loaded XSD schema for {format_type} v{version}")
        return schema
    except Exception as e:
        logger.error(f"Failed to load XSD schema: {str(e)}")
        return None


def validate_xml_with_schema(xml_path: str, 
                             format_type: str = "default", 
                             version: str = "1") -> Dict[str, Any]:
    """
    Validate an XML file against the appropriate XSD schema.
    
    Args:
        xml_path: Path to the XML file
        format_type: XML format type
        version: Schema version
        
    Returns:
        Dict[str, Any]: Validation results with keys:
            - valid (bool): Whether validation passed
            - errors (list): List of validation errors if any
    """
    result = {
        "valid": False,
        "errors": []
    }
    
    # Check if file exists
    if not os.path.exists(xml_path):
        result["errors"].append(f"XML file not found: {xml_path}")
        return result
    
    # Load schema
    schema = load_xsd_schema(format_type, version)
    if schema is None:
        result["errors"].append(f"No schema available for {format_type} v{version}")
        return result
    
    try:
        # Parse XML
        xml_doc = etree.parse(xml_path)
        
        # Validate against schema
        is_valid = schema.validate(xml_doc)
        result["valid"] = is_valid
        
        # Collect errors if validation failed
        if not is_valid:
            for error in schema.error_log:
                result["errors"].append(f"Line {error.line}: {error.message}")
        
        return result
    except Exception as e:
        result["errors"].append(f"Validation error: {str(e)}")
        return result


def detect_format_and_version(xml_path: str) -> Dict[str, str]:
    """
    Detect the format type and version from an XML file.
    
    Args:
        xml_path: Path to the XML file
        
    Returns:
        Dict[str, str]: Dictionary with format_type and version keys
    """
    result = {
        "format_type": "default",
        "version": "1"
    }
    
    try:
        # Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Check for format indicators
        if root.tag == "project" and root.find(".//premiere") is not None:
            result["format_type"] = "premiere"
        elif root.tag == "fcpxml" or root.find(".//fcpxml") is not None:
            result["format_type"] = "fcpxml"
        elif root.find(".//davinci_resolve") is not None:
            result["format_type"] = "davinci"
        elif root.find(".//jianying") is not None or root.find(".//info/metadata/jy_type") is not None:
            result["format_type"] = "jianying"
            
        # Try to extract version information
        version_node = root.find(".//version") or root.find(".//format_version")
        if version_node is not None and version_node.text:
            version_text = version_node.text.strip()
            # Extract the first digit of the version
            version_match = re.search(r'(\d+)', version_text)
            if version_match:
                result["version"] = version_match.group(1)
                
    except Exception as e:
        logger.error(f"Error detecting format: {str(e)}")
        
    return result


def create_schema_directory() -> bool:
    """
    Create the directory for XSD schema files if it doesn't exist.
    
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    schema_dir = project_root / "configs"
    
    try:
        if not schema_dir.exists():
            schema_dir.mkdir(parents=True)
            logger.info(f"Created schema directory: {schema_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to create schema directory: {str(e)}")
        return False


def clear_schema_cache() -> None:
    """Clear the schema cache."""
    global _schema_cache
    _schema_cache = {}
    logger.info("Schema cache cleared")


if __name__ == "__main__":
    # If run as a script, demonstrate schema loading
    import argparse
    
    parser = argparse.ArgumentParser(description='XSD Schema Loader')
    parser.add_argument('--format', help='Format type (premiere, fcpxml, davinci, jianying)',
                       default='default')
    parser.add_argument('--version', help='Schema version', default='1')
    parser.add_argument('--validate', help='XML file to validate')
    
    args = parser.parse_args()
    
    # Create schema directory if needed
    create_schema_directory()
    
    if args.validate:
        # Validate specified XML file
        result = validate_xml_with_schema(args.validate, args.format, args.version)
        print(f"Validation {'passed' if result['valid'] else 'failed'}")
        if not result['valid']:
            for error in result['errors']:
                print(f"Error: {error}")
    else:
        # Just attempt to load the schema
        schema = load_xsd_schema(args.format, args.version)
        if schema is not None:
            print(f"Successfully loaded schema for {args.format} v{args.version}")
        else:
            print(f"Failed to load schema for {args.format} v{args.version}") 