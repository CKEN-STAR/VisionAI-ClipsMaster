#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("Simple audit test script")

import os
import sys
import tempfile
from pathlib import Path

print("Modules imported successfully")

try:
    temp_dir = tempfile.mkdtemp()
    print(f"Created temp directory: {temp_dir}")
    
    test_file = Path(temp_dir) / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    print(f"Created test file: {test_file}")
    
    with open(test_file, "r") as f:
        content = f.read()
    print(f"Read content: {content}")
    
    os.remove(test_file)
    os.rmdir(temp_dir)
    print("Cleanup successful")
    
    print("All tests passed!")
    sys.exit(0)
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 