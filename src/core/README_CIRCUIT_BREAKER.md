# Circuit Breaker Pattern in VisionAI-ClipsMaster

## Overview

The Circuit Breaker pattern is a stability pattern used in software engineering to prevent cascading failures in distributed systems. It's designed to detect failures and encapsulate the logic of preventing a failure from constantly recurring during maintenance, temporary external system failure, or unexpected system difficulties.

In VisionAI-ClipsMaster, the Circuit Breaker implementation helps:

1. Prevent excessive resource consumption when services are failing
2. Fail fast rather than waiting for timeouts
3. Provide fallback mechanisms during service outages
4. Allow graceful recovery with half-open state testing

## Implementation Features

Our Circuit Breaker implementation includes:

- Error rate threshold-based circuit breaking (default: >50% error rate triggers circuit breaking)
- Consecutive failures threshold-based fast circuit breaking (default: >10 failures triggers circuit breaking)
- Three circuit states (CLOSED, OPEN, HALF-OPEN) with automatic transitions
- A thread-safe registry to manage multiple circuit breaker instances
- Decorator support for easy application to API calls and other vulnerable operations
- Customizable timeouts, thresholds, and monitoring windows

## States

The Circuit Breaker has three states:

1. **CLOSED** - Normal operation, requests flow through and failures are monitored
2. **OPEN** - Circuit is tripped, all requests are immediately rejected without calling the protected operation
3. **HALF-OPEN** - Recovery testing state, limited requests are allowed through to test if the system has recovered

![Circuit Breaker States Diagram](https://raw.githubusercontent.com/yourusername/VisionAI-ClipsMaster/main/docs/images/circuit_breaker_states.png)

## State Transitions

- **CLOSED → OPEN**: Triggered when either:
  - Error rate exceeds the configured threshold (default 50%)
  - Consecutive failures exceed the threshold (default 10)

- **OPEN → HALF-OPEN**: Occurs automatically after the configured open duration (default 300 seconds)

- **HALF-OPEN → CLOSED**: Occurs when a limited number of test requests succeed

- **HALF-OPEN → OPEN**: Occurs if any request fails during the half-open state

## Usage Examples

### Method 1: Using the Decorator

```python
from src.core.circuit_breaker import circuit_breaker

# Simple usage with defaults
@circuit_breaker()
def call_external_api():
    # API call that might fail
    pass

# Customized settings
@circuit_breaker(
    name="critical_api",
    error_threshold_percentage=25.0,
    consecutive_failure_threshold=5,
    open_duration=60,
    fallback_function=lambda *args, **kwargs: {"error": "Service unavailable"}
)
def call_critical_api(param1, param2):
    # Critical API call with lower error tolerance
    pass
```

### Method 2: Direct Instance Usage

```python
from src.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

class ApiService:
    def __init__(self):
        self.breaker = CircuitBreaker(
            name="api_service",
            error_threshold_percentage=40.0,
            consecutive_failure_threshold=3
        )
        
    def call_api(self, endpoint):
        # Check if circuit allows request
        if not self.breaker.allow_request():
            return {"error": "Service temporarily unavailable"}
            
        try:
            # Make API call
            result = self._make_api_call(endpoint)
            
            # Record success
            self.breaker.on_success()
            return result
            
        except Exception as e:
            # Record failure
            self.breaker.on_failure()
            # Re-raise or handle exception
            raise
```

### Method 3: Using the Registry

```python
from src.core.circuit_breaker import CircuitBreakerRegistry

# Get registry singleton
registry = CircuitBreakerRegistry()

# Create/get circuit breakers
db_breaker = registry.create("database", consecutive_failure_threshold=5)
api_breaker = registry.create("external_api", error_threshold_percentage=30.0)

# Get all circuit breakers
all_breakers = registry.get_all()

# Get states of all circuit breakers for monitoring
states = registry.get_states()
```

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `name` | Circuit breaker name | Function name |
| `error_threshold_percentage` | Error rate that triggers circuit breaking | 50.0 |
| `consecutive_failure_threshold` | Consecutive failures that trigger fast circuit breaking | 10 |
| `open_duration` | Duration in seconds to keep the circuit breaker open | 300 |
| `half_open_max_calls` | Maximum concurrent calls allowed in half-open state | 3 |
| `reset_timeout` | Timeout in seconds to reset the circuit breaker after successful calls in half-open state | 60 |
| `monitoring_window` | Time window in seconds for monitoring error rate | 60 |
| `min_calls_for_error_rate` | Minimum number of calls required to calculate error rate | 10 |
| `fallback_function` | Function to call when circuit is open (decorator only) | None |

## Integration With System Monitoring

The Circuit Breaker pattern integrates with the VisionAI-ClipsMaster monitoring systems:

1. All circuit state changes are logged at appropriate levels
2. Circuit states can be queried for dashboard display
3. Circuit breaker metrics can be collected for trend analysis

## Common Use Cases

1. **External API Protection**: Prevent system overload when external APIs are slow or unresponsive
2. **Database Connection Protection**: Avoid excessive timeouts when database connections fail
3. **Resource-Intensive Operations**: Protect operations that consume significant CPU, memory, or GPU resources
4. **Cross-Service Communication**: Maintain stability when dependent services are degraded

## Best Practices

1. **Circuit Naming**: Use descriptive names for circuit breakers to easily identify them in logs and monitoring
2. **Threshold Tuning**: Start with higher thresholds and adjust down based on observation
3. **Monitoring**: Track circuit breaker states and transitions to identify unstable components
4. **Fallbacks**: Always provide meaningful fallback behavior when circuits are open
5. **Open Duration**: Set appropriate open durations based on the expected recovery time of the protected resource

## Example: Circuit Breaker Dashboard

Run `python src/examples/circuit_breaker_example.py` to see the Circuit Breaker in action.

For a complete dashboard monitoring all circuit breakers in the system, use:

```python
from src.core.circuit_breaker import CircuitBreakerRegistry

registry = CircuitBreakerRegistry()
states = registry.get_states()

# Example: Converting states to dashboard format
dashboard_data = [
    {
        "name": name,
        "state": state["state"],
        "error_rate": f"{state['error_rate']:.2f}%",
        "failures": state["consecutive_failures"],
        "duration": f"{state['state_duration']:.1f}s"
    }
    for name, state in states.items()
]
```

## Related Patterns

- **Retry Pattern**: Often used with Circuit Breaker for transient failures
- **Fallback Pattern**: Provides alternative functionality when a service is unavailable
- **Bulkhead Pattern**: Isolates failures to prevent them from cascading

## Further Reading

For more information on Circuit Breaker and related reliability patterns:

- [Martin Fowler's Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Release It! by Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/)
- [Microsoft Cloud Design Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) 