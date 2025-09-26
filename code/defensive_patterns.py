"""
Defensive Programming Patterns for VacayMate System

This module implements the defensive patterns outlined in Defend_The_System.md:
1. Resilient Output Parsing and Schema Validation
2. Circuit Breakers and Tool-Level Fallbacks
3. State Validation and Recovery Safeguards
4. Iteration Caps and Loop Detection
5. Exponential Backoff and Retry Logic
6. Resource Usage Limits and Tool Sandboxing
"""

import time
import random
import hashlib
import logging
import psutil
import signal
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from functools import wraps
from collections import deque
from pydantic import BaseModel, Field, validator
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# 1. RESILIENT OUTPUT VALIDATION
# ===============================

class ValidatedLLMResponse(BaseModel):
    """Base class for validated LLM responses with automatic error correction."""
    
    @validator('*', pre=True)
    def clean_strings(cls, v):
        """Clean and validate string inputs."""
        if isinstance(v, str):
            return v.strip() or "[MISSING]"
        return v

class ValidatedFlightResponse(BaseModel):
    """Validated flight search response with fallbacks."""
    success: bool = Field(default=True)
    flights: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = Field(default=0)
    error: Optional[str] = None
    
    @validator("count")
    def validate_count(cls, v, values):
        """Ensure count matches flights list length."""
        flights = values.get("flights", [])
        return len(flights) if isinstance(flights, list) else 0
    
    @validator("success")
    def validate_success(cls, v, values):
        """Set success based on presence of flights and absence of errors."""
        has_flights = bool(values.get("flights"))
        has_error = bool(values.get("error"))
        return has_flights and not has_error

class ValidatedHotelResponse(BaseModel):
    """Validated hotel search response with fallbacks."""
    query: str = Field(default="[MISSING]")
    check_in_date: str = Field(default="")
    check_out_date: str = Field(default="")
    total_found: int = Field(default=0)
    hotels: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    
    @validator("total_found")
    def validate_total_found(cls, v, values):
        """Ensure total_found matches hotels list length."""
        hotels = values.get("hotels", [])
        return len(hotels) if isinstance(hotels, list) else 0

class ValidatedWeatherResponse(BaseModel):
    """Validated weather forecast response with fallbacks."""
    forecasts: List[Dict[str, Any]] = Field(default_factory=list)
    human_readable_summary: str = Field(default="Weather forecast unavailable")
    error: Optional[str] = None
    
    @validator("human_readable_summary")
    def ensure_summary(cls, v):
        """Provide fallback summary if missing."""
        return v.strip() or "Weather information is currently unavailable"

# ===============================
# 2. CIRCUIT BREAKERS
# ===============================

class ToolCircuitBreaker:
    """Circuit breaker for external tool calls with fallback strategies."""
    
    def __init__(self, failure_threshold: int = 5, timeout_minutes: int = 10):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_minutes * 60
        self.failure_counts = {}
        self.disabled_until = {}
        self.last_success = {}
    
    def call_tool(self, tool_name: str, tool_func: Callable, fallback_func: Callable, *args, **kwargs):
        """
        Call a tool with circuit breaker protection.
        
        Args:
            tool_name: Unique identifier for the tool
            tool_func: The actual tool function to call
            fallback_func: Fallback function to use when circuit is open
            *args, **kwargs: Arguments to pass to the tool function
        """
        # Check if tool is disabled
        if tool_name in self.disabled_until:
            if time.time() < self.disabled_until[tool_name]:
                logger.warning(f"Circuit breaker OPEN for {tool_name}, using fallback")
                return fallback_func(*args, **kwargs)
            else:
                # Re-enable tool
                del self.disabled_until[tool_name]
                logger.info(f"Circuit breaker CLOSED for {tool_name}, re-enabling")
        
        try:
            result = tool_func(*args, **kwargs)
            
            # Reset failure count on success
            self.failure_counts[tool_name] = 0
            self.last_success[tool_name] = time.time()
            
            return result
            
        except Exception as e:
            # Increment failure count
            self.failure_counts[tool_name] = self.failure_counts.get(tool_name, 0) + 1
            
            logger.error(f"Tool {tool_name} failed (attempt {self.failure_counts[tool_name]}): {e}")
            
            # Check if we should trip the circuit
            if self.failure_counts[tool_name] >= self.failure_threshold:
                self.disabled_until[tool_name] = time.time() + self.timeout_seconds
                logger.error(f"Circuit breaker TRIPPED for {tool_name}, disabled for {self.timeout_seconds/60} minutes")
                return fallback_func(*args, **kwargs)
            
            # Re-raise if under threshold
            raise e
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all circuit breakers."""
        now = time.time()
        status = {}
        
        for tool_name in set(list(self.failure_counts.keys()) + list(self.disabled_until.keys())):
            is_disabled = tool_name in self.disabled_until and now < self.disabled_until[tool_name]
            status[tool_name] = {
                "failures": self.failure_counts.get(tool_name, 0),
                "disabled": is_disabled,
                "disabled_until": self.disabled_until.get(tool_name),
                "last_success": self.last_success.get(tool_name)
            }
        
        return status

# Global circuit breaker instance
circuit_breaker = ToolCircuitBreaker()

# ===============================
# 3. STATE VALIDATION
# ===============================

def validate_and_fix_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and repair VacayMate state before processing.
    
    Args:
        state: The current state dictionary
        
    Returns:
        Dict: Validated and repaired state
    """
    # Ensure required keys exist
    required_keys = [
        "user_request", "current_location", "destination", 
        "start_date", "return_date", "manager_messages",
        "researcher_messages", "calculator_messages", 
        "planner_messages", "summarizer_messages"
    ]
    
    for key in required_keys:
        if key not in state:
            if key.endswith("_messages"):
                state[key] = []
            else:
                state[key] = "[MISSING]"
            logger.warning(f"Missing key '{key}' in state, added default value")
    
    # Type validation for message lists
    for key in ["manager_messages", "researcher_messages", "calculator_messages", 
                "planner_messages", "summarizer_messages"]:
        if not isinstance(state.get(key), list):
            state[key] = []
            logger.warning(f"Fixed type for '{key}' in state")
    
    # Validate results dictionaries
    for key in ["research_results", "calculator_results", "planner_results"]:
        if key not in state:
            state[key] = {}
        elif not isinstance(state[key], dict):
            state[key] = {}
            logger.warning(f"Fixed type for '{key}' in state")
    
    # Truncate oversized message histories
    max_messages = 50
    for key in ["manager_messages", "researcher_messages", "calculator_messages", 
                "planner_messages", "summarizer_messages"]:
        messages = state.get(key, [])
        if len(messages) > max_messages:
            state[key] = messages[-max_messages:]
            logger.info(f"Truncated {key} to last {max_messages} messages")
    
    # Validate boolean flags
    if "plan_approved" not in state:
        state["plan_approved"] = False
    elif not isinstance(state["plan_approved"], bool):
        state["plan_approved"] = False
        logger.warning("Fixed plan_approved type in state")
    
    return state

def safe_state_transition(process_func: Callable) -> Callable:
    """
    Decorator for safe state transitions with validation and error recovery.
    
    Args:
        process_func: The function that processes the state
        
    Returns:
        Callable: Wrapped function with state validation
    """
    @wraps(process_func)
    def wrapper(state: Dict[str, Any], *args, **kwargs):
        try:
            # Validate state before processing
            state = validate_and_fix_state(state)
            
            # Process the state
            result = process_func(state, *args, **kwargs)
            
            # Validate state after processing
            if isinstance(result, dict):
                result = validate_and_fix_state(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in state transition: {e}")
            
            # Return a safe fallback state
            safe_state = validate_and_fix_state(state)
            safe_state.update({
                "error": str(e),
                "status": "recovered",
                "last_error_time": datetime.now().isoformat()
            })
            
            return safe_state
    
    return wrapper

# ===============================
# 4. ITERATION CAPS & LOOP DETECTION
# ===============================

class LoopDetector:
    """Advanced loop detection with state fingerprinting."""
    
    def __init__(self, max_iterations: int = 10, history_size: int = 5):
        self.max_iterations = max_iterations
        self.state_history = deque(maxlen=history_size)
        self.iteration_count = 0
        self.start_time = time.time()
    
    def check_loop(self, state: Dict[str, Any]) -> str:
        """
        Check for loops and iteration limits.
        
        Returns:
            str: "continue", "max_iterations_exceeded", or "loop_detected"
        """
        self.iteration_count += 1
        
        # Check iteration limit
        if self.iteration_count > self.max_iterations:
            logger.error(f"Maximum iterations ({self.max_iterations}) exceeded")
            return "max_iterations_exceeded"
        
        # Create state fingerprint
        state_key = self._create_state_fingerprint(state)
        
        # Check for repeated states (loop detection)
        if state_key in self.state_history:
            logger.error(f"Loop detected at iteration {self.iteration_count}")
            return "loop_detected"
        
        self.state_history.append(state_key)
        return "continue"
    
    def _create_state_fingerprint(self, state: Dict[str, Any]) -> str:
        """Create a hash of relevant state components."""
        relevant_data = {
            "query": state.get("user_request", ""),
            "destination": state.get("destination", ""),
            "current_step": state.get("current_step", ""),
            "last_action": state.get("last_action", ""),
            "message_count": len(state.get("manager_messages", []))
        }
        return hashlib.md5(str(relevant_data).encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current loop detection statistics."""
        return {
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
            "runtime_seconds": time.time() - self.start_time,
            "state_history_size": len(self.state_history)
        }

def with_loop_detection(max_iterations: int = 10):
    """Decorator to add loop detection to node functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(state: Dict[str, Any], *args, **kwargs):
            # Get or create loop detector
            detector = state.get("_loop_detector")
            if not detector:
                detector = LoopDetector(max_iterations=max_iterations)
                state["_loop_detector"] = detector
            
            # Check for loops
            loop_status = detector.check_loop(state)
            
            if loop_status == "max_iterations_exceeded":
                return {
                    **state,
                    "status": "terminated",
                    "reason": "Maximum iterations exceeded",
                    "final_plan": "Process terminated due to iteration limit. Partial results may be available.",
                    "_loop_stats": detector.get_stats()
                }
            elif loop_status == "loop_detected":
                return {
                    **state,
                    "status": "terminated",
                    "reason": "Infinite loop detected",
                    "final_plan": "Process terminated due to loop detection. Partial results may be available.",
                    "_loop_stats": detector.get_stats()
                }
            
            # Continue normal processing
            return func(state, *args, **kwargs)
        
        return wrapper
    return decorator

# ===============================
# 5. EXPONENTIAL BACKOFF & RETRY
# ===============================

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      backoff_factor: float = 2.0, max_delay: float = 60.0,
                      retryable_exceptions: Tuple = (requests.RequestException, TimeoutError)):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay (2 = double each time)
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exceptions that should trigger retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise e
                    
                    # Calculate delay with jitter
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    jitter = random.uniform(0.8, 1.2) * delay
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {jitter:.2f}s")
                    time.sleep(jitter)
                    
                except Exception as e:
                    # Non-retryable exception, fail immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise e
            
            raise last_exception
        return wrapper
    return decorator

# ===============================
# 6. RESOURCE LIMITS
# ===============================

def resource_limited(max_memory_mb: int = 500, max_time_seconds: int = 30):
    """
    Decorator to limit resource usage of functions.
    
    Args:
        max_memory_mb: Maximum memory usage in MB
        max_time_seconds: Maximum execution time in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} exceeded {max_time_seconds}s limit")
            
            # Set timeout (Unix only)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(max_time_seconds)
            
            try:
                result = func(*args, **kwargs)
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_used = current_memory - initial_memory
                
                if memory_used > max_memory_mb:
                    logger.warning(f"Function {func.__name__} used {memory_used:.1f}MB (limit: {max_memory_mb}MB)")
                
                return result
                
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)  # Cancel timeout
        
        return wrapper
    return decorator

# ===============================
# FALLBACK FUNCTIONS
# ===============================

def flight_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback function for flight search failures."""
    return ValidatedFlightResponse(
        success=False,
        flights=[],
        count=0,
        error="Flight search service temporarily unavailable. Using cached or default data."
    ).dict()

def hotel_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback function for hotel search failures."""
    return ValidatedHotelResponse(
        query=kwargs.get("query", "[MISSING]"),
        check_in_date=str(kwargs.get("check_in_date", "")),
        check_out_date=str(kwargs.get("check_out_date", "")),
        total_found=0,
        hotels=[],
        error="Hotel search service temporarily unavailable. Using cached or default data."
    ).dict()

def weather_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback function for weather forecast failures."""
    return ValidatedWeatherResponse(
        forecasts=[],
        human_readable_summary="Weather forecast is currently unavailable. Please check local weather services.",
        error="Weather service temporarily unavailable."
    ).dict()

# ===============================
# UTILITY FUNCTIONS
# ===============================

def safe_api_call(tool_name: str, api_func: Callable, fallback_func: Callable, 
                 *args, **kwargs) -> Dict[str, Any]:
    """
    Safely call an API with circuit breaker, retry logic, and validation.
    
    Args:
        tool_name: Name of the tool for circuit breaker tracking
        api_func: The API function to call
        fallback_func: Fallback function if API fails
        *args, **kwargs: Arguments for the API function
    """
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @resource_limited(max_memory_mb=100, max_time_seconds=30)
    def protected_api_call():
        return api_func(*args, **kwargs)
    
    return circuit_breaker.call_tool(
        tool_name=tool_name,
        tool_func=protected_api_call,
        fallback_func=fallback_func,
        *args, **kwargs
    )

def get_system_health() -> Dict[str, Any]:
    """Get overall system health status."""
    return {
        "circuit_breakers": circuit_breaker.get_status(),
        "timestamp": datetime.now().isoformat(),
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024
    }

# ===============================
# TESTING UTILITIES
# ===============================

def simulate_api_failure():
    """Utility function to simulate API failures for testing."""
    raise requests.RequestException("Simulated API failure for testing")

def test_circuit_breaker():
    """Test the circuit breaker functionality."""
    def failing_function():
        raise Exception("Test failure")
    
    def fallback_function():
        return {"status": "fallback", "message": "Using fallback data"}
    
    # Test multiple failures
    for i in range(7):
        try:
            result = circuit_breaker.call_tool("test_tool", failing_function, fallback_function)
            print(f"Attempt {i+1}: {result}")
        except Exception as e:
            print(f"Attempt {i+1}: Exception - {e}")
    
    # Check status
    print("Circuit breaker status:", circuit_breaker.get_status())

# ===============================
# API RESPONSE VALIDATION MODELS
# ===============================

class ValidatedFlightResponse(BaseModel):
    """Pydantic model for validating flight API responses."""
    success: bool = Field(default=True, description="Whether the flight search was successful")
    flights: List[Dict[str, Any]] = Field(default_factory=list, description="List of flight options")
    count: int = Field(default=0, description="Number of flights found")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    @validator('count', pre=True, always=True)
    def validate_count(cls, v, values):
        if 'flights' in values:
            return len(values['flights'])
        return v or 0
    
    @validator('success', pre=True, always=True)
    def validate_success(cls, v, values):
        if 'error' in values and values['error']:
            return False
        return v if v is not None else True

class ValidatedHotelResponse(BaseModel):
    """Pydantic model for validating hotel API responses."""
    hotels: List[Dict[str, Any]] = Field(default_factory=list, description="List of hotel options")
    query: str = Field(default="", description="Search query used")
    check_in_date: Optional[str] = Field(default=None, description="Check-in date")
    check_out_date: Optional[str] = Field(default=None, description="Check-out date")
    total_found: int = Field(default=0, description="Total number of hotels found")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    @validator('total_found', pre=True, always=True)
    def validate_total_found(cls, v, values):
        if 'hotels' in values:
            return len(values['hotels'])
        return v or 0

class ValidatedWeatherResponse(BaseModel):
    """Pydantic model for validating weather API responses."""
    forecasts: List[Dict[str, Any]] = Field(default_factory=list, description="Weather forecast data")
    human_readable_summary: str = Field(default="", description="Human readable weather summary")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    @validator('human_readable_summary', pre=True, always=True)
    def validate_summary(cls, v, values):
        if not v and 'forecasts' in values and values['forecasts']:
            return f"Weather forecast available for {len(values['forecasts'])} days"
        return v or "Weather information unavailable"

class ValidatedEventResponse(BaseModel):
    """Pydantic model for validating event API responses."""
    events: List[Dict[str, Any]] = Field(default_factory=list, description="List of events")
    query: str = Field(default="", description="Search query used")
    total_found: int = Field(default=0, description="Total number of events found")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    @validator('total_found', pre=True, always=True)
    def validate_total_found(cls, v, values):
        if 'events' in values:
            return len(values['events'])
        return v or 0

class ValidatedDestinationResponse(BaseModel):
    """Pydantic model for validating destination info API responses."""
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Destination information results")
    query: str = Field(default="", description="Search query used")
    error: Optional[str] = Field(default=None, description="Error message if any")

if __name__ == "__main__":
    # Run basic tests
    print("Testing defensive patterns...")
    test_circuit_breaker()
    print("System health:", get_system_health())

