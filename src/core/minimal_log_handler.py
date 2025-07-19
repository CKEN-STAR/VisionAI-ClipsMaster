#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - Minimal LogHandler

A minimal implementation of the LogHandler class to avoid import issues
when testing the circuit breaker implementation.
"""

import os
import sys
import logging
from pathlib import Path

class LogHandler:
    """Minimal LogHandler implementation for testing purposes"""
    
    def __init__(self, logger_name: str, level: int = logging.INFO):
        """Initialize a logger with a given name and level"""
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        
        # Add console handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)

def get_logger(logger_name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger by name"""
    handler = LogHandler(logger_name, level)
    return handler.logger 