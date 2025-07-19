#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stream-based XML validator module

Provides a high-performance, memory-efficient validation solution for large XML files
by using iterative parsing instead of loading entire files into memory.

Key features:
1. Incremental XML parsing with minimal memory footprint
2. Progressive validation of elements as they are parsed
3. Integration with existing validation framework
4. Optimized for large XML files common in video editing projects

This module complements the existing xml_validator.py by providing stream-based
alternatives that are more efficient for large files.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Generator, Iterator
import xml.etree.ElementTree as ET
import logging

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
    from src.validation.xsd_schema_loader import (
        load_xsd_schema,
        detect_format_and_version
    )
    from src.export.xml_validator import validate_legal_nodes, validate_xml_structure
except ImportError:
    # Simple logging fallback
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)
    # Fallback functions if imports fail
    def load_xsd_schema(*args, **kwargs):
        return None
    def detect_format_and_version(*args, **kwargs):
        return {"format_type": "default", "version": "1"}
    def validate_legal_nodes(*args, **kwargs):
        return False
    def validate_xml_structure(*args, **kwargs):
        return False

# Configure logger
logger = get_logger("stream_xml_validator")


def iterparse_with_context(xml_path: str, events: Tuple[str, ...] = ('start', 'end')) -> Tuple[Iterator, ET.Element]:
    """
    Create an iterparse context with the root element for efficient XML parsing
    
    Args:
        xml_path: Path to XML file
        events: Events to listen for
        
    Returns:
        Tuple[Iterator, ET.Element]: Iterator and root element
    """
    context = ET.iterparse(xml_path, events=events)
    # Get an iterator
    iterator = iter(context)
    # Get the root element
    _, root = next(iterator)
    return iterator, root


def stream_validate_syntax(xml_path: str) -> bool:
    """
    Validate XML syntax by streaming the file
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        bool: Whether the XML syntax is valid
    """
    logger.info(f"Validating XML syntax using stream-based approach: {xml_path}")
    
    try:
        # We just need to iterate through the file - if there are syntax errors,
        # an exception will be raised during parsing
        for _, _ in ET.iterparse(xml_path):
            pass
        
        logger.info("XML syntax validation passed")
        return True
        
    except Exception as e:
        logger.error(f"XML syntax validation failed: {str(e)}")
        return False


def stream_detect_format(xml_path: str) -> Dict[str, str]:
    """
    Detect XML format by streaming through file
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        Dict[str, str]: Format information with format_type and version
    """
    result = {
        "format_type": "default",
        "version": "1"
    }
    
    try:
        # Parse only start elements to detect format quickly
        iterator, root = iterparse_with_context(xml_path, events=('start',))
        
        # Check root tag
        if root.tag == "fcpxml":
            result["format_type"] = "fcpxml"
        elif root.tag == "project":
            # Need to look for more elements to determine exact format
            for event, elem in iterator:
                if event == 'start':
                    if elem.tag == "premiere":
                        result["format_type"] = "premiere"
                        break
            
        # Look for version information
        for event, elem in iterator:
            if event == 'start':
                if elem.tag == "version" or elem.tag == "format_version":
                    if elem.text:
                        version_text = elem.text.strip()
                        # Extract first digit of version
                        version_match = re.search(r'(\d+)', version_text)
                        if version_match:
                            result["version"] = version_match.group(1)
                            break
                
                # Don't need to process the entire file
                if elem.tag in ("timeline", "resources", "sequences"):
                    # We've gone far enough to detect format
                    break
        
        return result
        
    except Exception as e:
        logger.error(f"Error detecting format using streaming approach: {str(e)}")
        return result


def stream_validate_legal_nodes(xml_path: str) -> bool:
    """
    Validate legal disclaimer nodes using streaming approach
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        bool: Whether the legal nodes are valid
    """
    logger.info(f"Validating legal nodes using stream approach: {xml_path}")
    
    disclaimer_found = False
    ai_generated_found = False
    
    try:
        # Only look for elements we care about
        for _, elem in ET.iterparse(xml_path, events=('end',)):
            # Check for disclaimer nodes specifically
            if elem.tag == "disclaimer":
                disclaimer_found = True
                
                # Check if disclaimer mentions AI generation
                if elem.text and "AI Generated" in elem.text:
                    ai_generated_found = True
                    # We found what we need, no need to continue
                    break
            
            # Clear element to free memory
            elem.clear()
        
        if not disclaimer_found:
            logger.error("Legal disclaimer node missing")
            return False
            
        if not ai_generated_found:
            logger.error("Legal disclaimer does not contain AI Generated marker")
            return False
            
        logger.info("Legal nodes validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Legal nodes validation failed: {str(e)}")
        return False


def stream_validate_structure(xml_path: str) -> bool:
    """
    Validate XML structure using streaming approach
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        bool: Whether the structure is valid
    """
    logger.info(f"Validating XML structure using stream approach: {xml_path}")
    
    required_elements = {
        "project": False,
        "resources": False,
        "timeline": False
    }
    
    try:
        # Check if root element is project
        iterator, root = iterparse_with_context(xml_path, events=('start',))
        
        if root.tag == "project":
            required_elements["project"] = True
        
        # Look for required elements
        for event, elem in iterator:
            if event == 'start':
                if elem.tag in required_elements:
                    required_elements[elem.tag] = True
                
                # If we've found all required elements, we can stop
                if all(required_elements.values()):
                    break
            
            # Clear element to free memory
            elem.clear()
        
        # Check results
        missing_elements = [elem for elem, exists in required_elements.items() if not exists]
        
        if missing_elements:
            logger.error(f"XML structure incomplete. Missing elements: {', '.join(missing_elements)}")
            return False
            
        logger.info("XML structure validation passed")
        return True
        
    except Exception as e:
        logger.error(f"XML structure validation failed: {str(e)}")
        return False


def stream_validate_xml(xml_path: str, strict: bool = False) -> Dict[str, bool]:
    """
    Comprehensive XML validation using streaming approach
    
    Args:
        xml_path: Path to XML file
        strict: Whether to use strict validation mode
        
    Returns:
        Dict[str, bool]: Validation results
    """
    logger.info(f"Starting stream-based XML validation: {xml_path}")
    
    # Validation results
    results = {
        "exists": os.path.exists(xml_path),
        "legal_nodes": False,
        "structure": False,
        "syntax": False,
        "schema": False  # Schema validation is complex for streaming approach
    }
    
    # File existence validation
    if not results["exists"]:
        logger.error(f"XML file does not exist: {xml_path}")
        return results
    
    # XML syntax validation
    results["syntax"] = stream_validate_syntax(xml_path)
    if not results["syntax"]:
        logger.error("XML syntax validation failed, skipping remaining checks")
        return results
    
    # Legal nodes validation
    results["legal_nodes"] = stream_validate_legal_nodes(xml_path)
    
    # Structure validation
    results["structure"] = stream_validate_structure(xml_path)
    
    # Schema validation using existing code
    # Note: Full schema validation is difficult to implement with streaming approach
    # We use the existing module for this part
    try:
        from src.validation.xsd_schema_loader import validate_xml_with_schema
        
        # Detect format and version
        format_info = stream_detect_format(xml_path)
        format_type = format_info["format_type"]
        version = format_info["version"]
        
        logger.info(f"Detected XML format: {format_type}, version: {version}")
        
        # Validate with schema - this will still load the full XML but is unavoidable
        # for full XSD schema validation with the current implementation
        validation_result = validate_xml_with_schema(xml_path, format_type, version)
        results["schema"] = validation_result["valid"]
        
        if not results["schema"]:
            logger.error("Schema validation failed")
            for error in validation_result["errors"]:
                logger.error(f"  - {error}")
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
    
    # Overall validation result
    is_valid = all(results.values()) if strict else (results["exists"] and results["syntax"])
    
    if is_valid:
        logger.info("XML validation passed")
    else:
        logger.warning("XML validation did not pass all checks")
    
    return results


def memory_efficient_validation(xml_path: str, strict: bool = False, 
                               max_file_size: int = 10 * 1024 * 1024) -> Dict[str, bool]:
    """
    Smart validation function that decides whether to use streaming or regular approach
    based on file size
    
    Args:
        xml_path: Path to XML file
        strict: Whether to use strict validation
        max_file_size: Maximum file size in bytes for regular validation (default: 10MB)
        
    Returns:
        Dict[str, bool]: Validation results
    """
    # Check if file exists
    if not os.path.exists(xml_path):
        logger.error(f"File does not exist: {xml_path}")
        return {"exists": False}
    
    # Get file size
    file_size = os.path.getsize(xml_path)
    
    # Choose validation method based on file size
    if file_size > max_file_size:
        logger.info(f"Using stream-based validation for large file ({file_size/1024/1024:.2f} MB)")
        return stream_validate_xml(xml_path, strict)
    else:
        # Use regular validation for smaller files
        logger.info(f"Using regular validation for small file ({file_size/1024/1024:.2f} MB)")
        from src.export.xml_validator import validate_export_xml
        return validate_export_xml(xml_path, strict)


if __name__ == "__main__":
    # If run as a script, demonstrate usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Stream-based XML Validator')
    parser.add_argument('--xml', required=True, help='XML file to validate')
    parser.add_argument('--strict', action='store_true', help='Use strict validation')
    parser.add_argument('--max-size', type=int, default=10, 
                        help='Maximum file size in MB for regular validation')
    
    args = parser.parse_args()
    
    result = memory_efficient_validation(
        args.xml, 
        args.strict, 
        args.max_size * 1024 * 1024
    )
    
    print("\nValidation Results:")
    for key, value in result.items():
        print(f"  - {key}: {'PASS' if value else 'FAIL'}") 