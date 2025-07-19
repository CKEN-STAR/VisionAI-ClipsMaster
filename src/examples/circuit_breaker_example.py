#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - Circuit Breaker Pattern Example

This example demonstrates how to use the circuit breaker pattern to protect API calls
and other potentially unreliable operations from cascading failures.
"""

import os
import sys
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.core.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerRegistry, 
    circuit_breaker, 
    CircuitBreakerOpen
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("circuit_breaker_example")


# Example 1: Using the circuit breaker decorator
@circuit_breaker(
    name="example_api_call",
    error_threshold_percentage=50.0,
    consecutive_failure_threshold=5,
    open_duration=10  # Short duration for testing
)
def unreliable_api_call(should_fail: bool = False) -> Dict[str, Any]:
    """
    Simulates an unreliable API call
    
    Args:
        should_fail: If True, the call will fail
        
    Returns:
        Dict with response data
    """
    if should_fail:
        logger.warning("API call failed")
        raise Exception("API call failed")
        
    return {"status": "success", "data": "API response data"}


# Example 2: Using the circuit breaker directly
class ApiService:
    """Example service that uses an external API with circuit breaker protection"""
    
    def __init__(self):
        # Create a circuit breaker
        self.breaker = CircuitBreaker(
            name="api_service",
            error_threshold_percentage=40.0,
            consecutive_failure_threshold=3,
            open_duration=15  # Short duration for testing
        )
        
        # Register it with the registry
        registry = CircuitBreakerRegistry()
        registry.register(self.breaker)
        
    def call_api(self, endpoint: str, failure_probability: float = 0.0) -> Dict[str, Any]:
        """
        Call an API endpoint with circuit breaker protection
        
        Args:
            endpoint: API endpoint to call
            failure_probability: Probability of failure (0.0-1.0)
            
        Returns:
            API response
            
        Raises:
            CircuitBreakerOpen: If the circuit breaker is open
        """
        # Check if circuit breaker allows the request
        if not self.breaker.allow_request():
            raise CircuitBreakerOpen("api_service", self.breaker.open_until)
            
        try:
            # Simulate API call with possible failure
            if random.random() < failure_probability:
                logger.warning(f"API call to {endpoint} failed")
                raise Exception(f"API call to {endpoint} failed")
                
            # Simulate successful API call
            logger.info(f"API call to {endpoint} succeeded")
            response = {"status": "success", "endpoint": endpoint, "data": "API response data"}
            
            # Record success with the circuit breaker
            self.breaker.on_success()
            return response
            
        except Exception as e:
            # Record failure with the circuit breaker
            self.breaker.on_failure()
            # Re-raise the exception
            raise


def demonstrate_decorator_usage():
    """Demonstrate using the circuit breaker decorator"""
    logger.info("\n=== DEMONSTRATING CIRCUIT BREAKER DECORATOR ===")
    
    # Make successful calls
    logger.info("Making successful API calls...")
    for i in range(3):
        try:
            response = unreliable_api_call(should_fail=False)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")
    
    # Make failing calls to trigger circuit breaker
    logger.info("\nMaking failing API calls to trigger circuit breaker...")
    for i in range(10):
        try:
            response = unreliable_api_call(should_fail=True)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")
            
    # Try to make calls when circuit breaker is open
    logger.info("\nTrying calls with circuit breaker open...")
    for i in range(3):
        try:
            response = unreliable_api_call(should_fail=False)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")
    
    # Wait for circuit breaker to transition to half-open
    logger.info("\nWaiting for circuit breaker to transition to half-open state...")
    time.sleep(12)  # Longer than open_duration
    
    # Make successful calls to close the circuit breaker
    logger.info("\nMaking successful calls to close the circuit breaker...")
    for i in range(3):
        try:
            response = unreliable_api_call(should_fail=False)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")


def demonstrate_direct_usage():
    """Demonstrate using the circuit breaker directly"""
    logger.info("\n=== DEMONSTRATING DIRECT CIRCUIT BREAKER USAGE ===")
    
    # Create a service with circuit breaker
    service = ApiService()
    
    # Make successful calls
    logger.info("Making successful API calls...")
    for i in range(3):
        try:
            response = service.call_api(f"example/endpoint/{i}", failure_probability=0.0)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")
    
    # Make calls with increasing failure probability
    logger.info("\nMaking API calls with high failure probability...")
    for i in range(10):
        try:
            response = service.call_api(f"example/endpoint/{i}", failure_probability=0.8)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")
    
    # Wait for circuit breaker to transition to half-open
    logger.info("\nWaiting for circuit breaker to transition to half-open state...")
    time.sleep(17)  # Longer than open_duration
    
    # Make successful calls to close the circuit breaker
    logger.info("\nMaking successful calls to close the circuit breaker...")
    for i in range(5):
        try:
            response = service.call_api(f"example/endpoint/{i}", failure_probability=0.0)
            logger.info(f"Call {i+1} succeeded: {response}")
        except CircuitBreakerOpen as e:
            logger.error(f"Call {i+1} rejected: {str(e)}")
        except Exception as e:
            logger.error(f"Call {i+1} failed: {str(e)}")
    
    # Get circuit breaker state
    state = service.breaker.get_state()
    logger.info(f"\nFinal circuit breaker state: {state}")


def demonstrate_registry():
    """Demonstrate using the circuit breaker registry"""
    logger.info("\n=== DEMONSTRATING CIRCUIT BREAKER REGISTRY ===")
    
    # Get the registry
    registry = CircuitBreakerRegistry()
    
    # Create several circuit breakers
    registry.create("service_a", consecutive_failure_threshold=5)
    registry.create("service_b", error_threshold_percentage=30.0)
    registry.create("service_c", open_duration=60)
    
    # Get all circuit breakers
    breakers = registry.get_all()
    logger.info(f"Registered circuit breakers: {', '.join(breakers.keys())}")
    
    # Get states of all circuit breakers
    states = registry.get_states()
    for name, state in states.items():
        logger.info(f"Circuit breaker '{name}' state: {state['state']}")
    
    # Get a specific circuit breaker
    service_a = registry.get("service_a")
    logger.info(f"Retrieved circuit breaker: {service_a}")


if __name__ == "__main__":
    # Run the demonstrations
    demonstrate_decorator_usage()
    demonstrate_direct_usage()
    demonstrate_registry()
    
    logger.info("\nCircuit breaker demonstration completed.") 