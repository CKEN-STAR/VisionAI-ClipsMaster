#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - Circuit Breaker Pattern Implementation

Provides a robust implementation of the circuit breaker pattern for reliability engineering,
preventing the system from continuously attempting operations that are likely to fail,
thereby avoiding resource depletion and cascade failures. Supports both error rate-based
and consecutive failures-based circuit breaking strategies.
"""

import os
import sys
import time
import json
import logging
import threading
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

try:
    from src.utils.log_handler import LogHandler
except ImportError:
    # If project logging module can't be imported, use standard logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("circuit_breaker")
else:
    # Use project logger
    log_handler = LogHandler("circuit_breaker")
    logger = log_handler.logger


class CircuitState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = 0    # Closed state, requests are allowed through
    OPEN = 1      # Open state, requests are blocked
    HALF_OPEN = 2 # Half-open state, limited requests allowed through to test service recovery


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open
    
    When the circuit breaker is in open state, this exception is raised
    to prevent requests from going through
    """
    def __init__(self, circuit_name: str, open_until: Optional[datetime] = None):
        self.circuit_name = circuit_name
        self.open_until = open_until
        
        if open_until:
            time_remaining = (open_until - datetime.now()).total_seconds()
            message = f"Circuit breaker '{circuit_name}' is open, will try half-open in {time_remaining:.2f} seconds"
        else:
            message = f"Circuit breaker '{circuit_name}' is open"
            
        super().__init__(message)


class CircuitBreaker:
    """Circuit breaker implementation
    
    Supports both error rate-based and consecutive failures fast circuit breaking strategies
    """
    
    def __init__(self, name: str,
                 error_threshold_percentage: float = 50.0,
                 consecutive_failure_threshold: int = 10,
                 open_duration: int = 300,
                 half_open_max_calls: int = 3,
                 reset_timeout: int = 60,
                 monitoring_window: int = 60,
                 min_calls_for_error_rate: int = 10):
        """
        Initialize the circuit breaker
        
        Args:
            name: Circuit breaker name
            error_threshold_percentage: Error rate threshold percentage (0-100) that will trigger circuit breaking
            consecutive_failure_threshold: Consecutive failures threshold that will trigger fast circuit breaking
            open_duration: Duration in seconds to keep the circuit breaker open
            half_open_max_calls: Maximum concurrent calls allowed in half-open state
            reset_timeout: Timeout in seconds to reset the circuit breaker after successful calls in half-open state
            monitoring_window: Time window in seconds for monitoring error rate
            min_calls_for_error_rate: Minimum number of calls required to calculate error rate
        """
        self.name = name
        self.error_threshold_percentage = error_threshold_percentage
        self.consecutive_failure_threshold = consecutive_failure_threshold
        self.open_duration = open_duration
        self.half_open_max_calls = half_open_max_calls
        self.reset_timeout = reset_timeout
        self.monitoring_window = monitoring_window
        self.min_calls_for_error_rate = min_calls_for_error_rate
        
        # State variables
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.open_until = None
        self.consecutive_failures = 0
        self.half_open_calls = 0
        
        # Request statistics
        self.total_requests = 0
        self.failed_requests = 0
        self.success_requests = 0
        self.request_history = []  # List of (timestamp, success) tuples
        
        # Thread safety lock
        self.state_lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{name}' initialized: error threshold={error_threshold_percentage}%, "
                    f"consecutive failure threshold={consecutive_failure_threshold}")
    
    def allow_request(self) -> bool:
        """
        Determine if a request is allowed through the circuit breaker
        
        Returns:
            bool: True if the request is allowed, False otherwise
        """
        with self.state_lock:
            now = datetime.now()
            
            if self.state == CircuitState.OPEN:
                # Check if it's time to transition to half-open state
                if now >= self.open_until:
                    logger.info(f"Circuit breaker '{self.name}' transitioning to half-open state")
                    self._transition_to_half_open()
                    return self._check_half_open()
                return False
                
            elif self.state == CircuitState.HALF_OPEN:
                return self._check_half_open()
                
            # Closed state always allows requests
            return True
    
    def _check_half_open(self) -> bool:
        """Check if a request is allowed in half-open state"""
        if self.half_open_calls < self.half_open_max_calls:
            self.half_open_calls += 1
            return True
        return False
        
    def on_success(self):
        """Record a successful request and update circuit breaker state"""
        with self.state_lock:
            now = datetime.now()
            self.total_requests += 1
            self.success_requests += 1
            self.request_history.append((now, True))
            self._prune_old_requests(now)
            
            # Reset consecutive failures counter
            self.consecutive_failures = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls -= 1
                
                # In half-open state, consider transitioning to closed state on successful requests
                if self.half_open_calls <= 0:
                    logger.info(f"Circuit breaker '{self.name}' confirmed service recovery, closing")
                    self._transition_to_closed()
    
    def on_failure(self):
        """Record a failed request and update circuit breaker state"""
        with self.state_lock:
            now = datetime.now()
            self.total_requests += 1
            self.failed_requests += 1
            self.request_history.append((now, False))
            self._prune_old_requests(now)
            
            # Increment consecutive failures counter
            self.consecutive_failures += 1
            
            if self.state == CircuitState.CLOSED:
                # Check if circuit breaking thresholds are reached
                error_rate = self._calculate_error_rate()
                recent_requests = len(self.request_history)
                
                logger.debug(f"Circuit breaker '{self.name}' current status: "
                           f"error rate={error_rate:.2f}%, consecutive failures={self.consecutive_failures}, "
                           f"requests={recent_requests}")
                
                # Error rate-based circuit breaking
                if (recent_requests >= self.min_calls_for_error_rate and 
                    error_rate >= self.error_threshold_percentage):
                    logger.warning(f"Circuit breaker '{self.name}' triggered by error rate: "
                                 f"{error_rate:.2f}% exceeds threshold {self.error_threshold_percentage}%")
                    self._trip_breaker(f"Error rate {error_rate:.2f}% exceeds threshold")
                
                # Consecutive failures fast circuit breaking
                elif self.consecutive_failures >= self.consecutive_failure_threshold:
                    logger.warning(f"Circuit breaker '{self.name}' triggered by consecutive failures: "
                                 f"{self.consecutive_failures} exceeds threshold "
                                 f"{self.consecutive_failure_threshold}")
                    self._trip_breaker(f"Consecutive failures {self.consecutive_failures} exceeds threshold")
            
            elif self.state == CircuitState.HALF_OPEN:
                # In half-open state, immediately reopen the circuit on failure
                logger.warning(f"Circuit breaker '{self.name}' detected failure in half-open state, reopening")
                self.half_open_calls -= 1
                self._trip_breaker("Failure detected in half-open state")
    
    def _trip_breaker(self, reason: str):
        """Trip the circuit breaker to open state"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.open_until = self.last_state_change + timedelta(seconds=self.open_duration)
        self.half_open_calls = 0
        
        logger.warning(f"Circuit breaker '{self.name}' opened: {reason}, "
                     f"will try half-open in {self.open_duration} seconds")
    
    def _transition_to_half_open(self):
        """Transition to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.half_open_calls = 0
    
    def _transition_to_closed(self):
        """Transition to closed state"""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.consecutive_failures = 0
        self.half_open_calls = 0
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if not self.request_history:
            return 0.0
            
        total = len(self.request_history)
        failures = sum(1 for _, success in self.request_history if not success)
        
        if total == 0:
            return 0.0
            
        return (failures / total) * 100.0
    
    def _prune_old_requests(self, now: datetime):
        """Remove requests outside of the monitoring window"""
        cutoff = now - timedelta(seconds=self.monitoring_window)
        self.request_history = [r for r in self.request_history if r[0] >= cutoff]
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        with self.state_lock:
            error_rate = self._calculate_error_rate()
            now = datetime.now()
            
            state_info = {
                "name": self.name,
                "state": self.state.name,
                "error_rate": error_rate,
                "consecutive_failures": self.consecutive_failures,
                "total_requests": self.total_requests,
                "recent_requests": len(self.request_history),
                "last_state_change": self.last_state_change.isoformat(),
                "state_duration": (now - self.last_state_change).total_seconds()
            }
            
            if self.state == CircuitState.OPEN and self.open_until:
                state_info["open_until"] = self.open_until.isoformat()
                state_info["remaining_open_time"] = (self.open_until - now).total_seconds()
            
            if self.state == CircuitState.HALF_OPEN:
                state_info["half_open_calls"] = self.half_open_calls
                state_info["half_open_max_calls"] = self.half_open_max_calls
                
            return state_info
    
    def __str__(self) -> str:
        """String representation of the circuit breaker"""
        state_info = self.get_state()
        return (f"CircuitBreaker('{self.name}', state={state_info['state']}, "
                f"error_rate={state_info['error_rate']:.2f}%, "
                f"consecutive_failures={state_info['consecutive_failures']})")
    
    def __repr__(self) -> str:
        return self.__str__()


class CircuitBreakerRegistry:
    """Circuit breaker registry to manage all circuit breaker instances"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitBreakerRegistry, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the circuit breaker registry"""
        if self._initialized:
            return
            
        self._breakers = {}  # name -> CircuitBreaker
        self._lock = threading.RLock()
        self._initialized = True
        
        logger.info("Circuit breaker registry initialized")
    
    def register(self, circuit_breaker: CircuitBreaker) -> CircuitBreaker:
        """Register a circuit breaker instance"""
        with self._lock:
            name = circuit_breaker.name
            if name in self._breakers:
                logger.warning(f"Circuit breaker '{name}' already exists, will be replaced")
            
            self._breakers[name] = circuit_breaker
            logger.info(f"Registered circuit breaker '{name}'")
            return circuit_breaker
    
    def unregister(self, name: str) -> bool:
        """Unregister a circuit breaker instance"""
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                logger.info(f"Unregistered circuit breaker '{name}'")
                return True
            return False
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name"""
        with self._lock:
            return self._breakers.get(name)
    
    def create(self, name: str, **kwargs) -> CircuitBreaker:
        """Create and register a new circuit breaker"""
        with self._lock:
            if name in self._breakers:
                logger.warning(f"Circuit breaker '{name}' already exists, returning existing instance")
                return self._breakers[name]
                
            circuit = CircuitBreaker(name=name, **kwargs)
            return self.register(circuit)
    
    def get_all(self) -> Dict[str, CircuitBreaker]:
        """Get all registered circuit breakers"""
        with self._lock:
            return self._breakers.copy()
    
    def get_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        with self._lock:
            return {name: breaker.get_state() for name, breaker in self._breakers.items()}


def circuit_breaker(name: Optional[str] = None, 
                    error_threshold_percentage: float = 50.0,
                    consecutive_failure_threshold: int = 10,
                    open_duration: int = 300,
                    fallback_function: Optional[Callable] = None,
                    **kwargs) -> Callable:
    """
    Circuit breaker decorator to protect function calls
    
    Args:
        name: Circuit breaker name, defaults to function name
        error_threshold_percentage: Error rate threshold, default 50%
        consecutive_failure_threshold: Consecutive failures threshold, default 10
        open_duration: Duration in seconds to keep the circuit open, default 300 seconds
        fallback_function: Fallback function to call when circuit is open
        **kwargs: Additional arguments to pass to CircuitBreaker
    
    Returns:
        Decorated function
    
    Example:
        @circuit_breaker(error_threshold_percentage=20.0)
        def api_call():
            # API call that might fail
            pass
    """
    registry = CircuitBreakerRegistry()
    
    def decorator(func):
        # Determine circuit breaker name
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        
        # Get or create circuit breaker
        breaker = registry.get(breaker_name) or registry.create(
            breaker_name,
            error_threshold_percentage=error_threshold_percentage,
            consecutive_failure_threshold=consecutive_failure_threshold,
            open_duration=open_duration,
            **kwargs
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if request is allowed
            if not breaker.allow_request():
                logger.warning(f"Circuit breaker '{breaker_name}' is open, rejecting request")
                
                # Call fallback if provided
                if fallback_function:
                    return fallback_function(*args, **kwargs)
                    
                # Otherwise raise exception
                raise CircuitBreakerOpen(breaker_name, breaker.open_until)
            
            # Execute protected function
            try:
                result = func(*args, **kwargs)
                breaker.on_success()
                return result
            except CircuitBreakerOpen:
                # Don't catch circuit breaker's own exceptions
                raise
            except Exception as e:
                # Record failure and re-raise exception
                breaker.on_failure()
                raise
        
        # Add reference to circuit breaker for debugging/testing
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


def get_registry() -> CircuitBreakerRegistry:
    """Get the circuit breaker registry singleton"""
    return CircuitBreakerRegistry() 