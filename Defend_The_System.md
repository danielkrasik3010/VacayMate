# Defend The System: Robust AI Agent Design Patterns

## Table of Contents
1. [Introduction](#introduction)
2. [Resilient Output Parsing and Schema Validation](#resilient-output-parsing-and-schema-validation)
3. [Circuit Breakers and Tool-Level Fallbacks](#circuit-breakers-and-tool-level-fallbacks)
4. [State Validation and Recovery Safeguards](#state-validation-and-recovery-safeguards)
5. [Iteration Caps and Loop Detection](#iteration-caps-and-loop-detection)
6. [Exponential Backoff and Retry Logic](#exponential-backoff-and-retry-logic)
7. [Resource Usage Limits and Tool Sandboxing](#resource-usage-limits-and-tool-sandboxing)
8. [Best Practices Summary](#best-practices-summary)

## Introduction

Building robust AI agents requires more than just connecting LLMs to tools. Production systems face numerous failure modes: malformed outputs, API timeouts, infinite loops, resource exhaustion, and corrupted state. This document outlines defensive programming patterns that make AI agents resilient to these common failure scenarios.

The patterns presented here follow a simple philosophy: **assume everything can and will fail, then design for graceful recovery**.

---

## Resilient Output Parsing and Schema Validation

### Problem
LLMs don't always return perfect JSON. Empty responses, malformed outputs, and missing fields can crash your pipeline.

### Solution
Enforce structure and apply validation logic upfront using Pydantic models with custom validators.

```python
from pydantic import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class Product(BaseModel):
name: str = Field(...)
price: float = Field(...)

@validator("price")
def fix_price(cls, v):
return max(0.01, v) if v > 0 else 0.01

@validator("name")
def clean_name(cls, v):
return v.strip() or "Unknown Product"

model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_template("""
Based on the catalog below, extract product info for: {description}

Catalog:
{catalog_data}
""")

chain = prompt | model.with_structured_output(Product)

result = chain.invoke({
    "description": "Two kilos of tomato",
    "catalog_data": "Tomato - $2.99/kg, Potato - $1.50/kg, Onion - $1.80/kg"
})
```

### Benefits
- LLM output is grounded in structured input
- Automatic validation and correction of malformed data
- Pipeline continues running even with imperfect responses

> 💡 **Key Insight**: Never assume the model got it right. Always validate before moving on.

---

## Circuit Breakers and Tool-Level Fallbacks

### Problem
Repeated API failures and tool execution errors can bring down your entire system. Continuously hammering a failing service wastes resources and provides no value.

### Solution
Implement circuit breakers that detect persistent failures and temporarily disable problematic tools, switching to backup options until the service recovers.

**Example Scenario**: What happens if a tool fails *every time* for 10 minutes straight?

A circuit breaker detects the persistent failure pattern and disables that tool temporarily, protecting the rest of the system:

```python
import time

class ToolCircuitBreaker:
    def __init__(self):
self.failure_counts = {}
self.disabled_until = {}

def call_tool(self, tool_name, tool_func, fallback_func):
        # Check if tool is disabled
if tool_name in self.disabled_until:
            if time.time() < self.disabled_until[tool_name]:
                return fallback_func()  # Still disabled, use fallback
else:
                del self.disabled_until[tool_name]  # Re-enable tool

try:
result = tool_func()
            self.failure_counts[tool_name] = 0  # Reset on success
return result
except Exception:
            self.failure_counts[tool_name] = self.failure_counts.get(tool_name, 0) + 1
            
            if self.failure_counts[tool_name] >= 5:
                # Disable tool for 10 minutes
                self.disabled_until[tool_name] = time.time() + (10 * 60)
return fallback_func()

            raise  # Re-raise if under threshold

# Usage Example
breaker = ToolCircuitBreaker()

def search_web():
return web_search_tool.invoke(query)

def use_cached_results():
return {"results": "Using cached data", "source": "fallback"}

result = breaker.call_tool("web_search", search_web, use_cached_results)
```

### How It Works
1. **Failure Tracking**: Count consecutive failures for each tool
2. **Circuit Tripping**: After 5 failures, disable the tool for 10 minutes
3. **Fallback Activation**: Use alternative data sources during downtime
4. **Auto-Recovery**: Automatically re-enable tools after the timeout period

### Benefits
- Prevents cascade failures from spreading
- Maintains system availability during partial outages
- Reduces unnecessary load on failing services
- Provides graceful degradation with fallback data

> 💡 **Key Insight**: Graceful degradation beats complete failure — every time

---

## State Validation and Recovery Safeguards

### Problem
Your agent's state is its memory. If it's corrupted — missing keys, wrong data types, or inconsistent values — the system will fail in weird, hard-to-debug ways.

### Solution
Defend your state like it's critical infrastructure. Because it is.

#### Core Principles
- **Always validate state** before passing to the next node
- **Use default values** when a key might be missing
- **Add sanity checks**: verify expected keys exist and have correct types
- **On failure, recover gracefully**: reset or truncate state safely
- **Log everything** for debugging and monitoring

#### Implementation Example

```python
def validate_and_fix_state(state):
    """Validate and repair agent state before processing"""
    
    # Ensure required keys exist
if "user_query" not in state:
        state["user_query"] = "[MISSING]"
        print("WARNING: Missing user_query in state")
    
    if "step" not in state:
        state["step"] = 0
        print("WARNING: Missing step counter in state")
    
    # Type validation
    if not isinstance(state.get("documents", []), list):
        state["documents"] = []
        print("WARNING: Fixed documents type in state")
    
    # Sanity checks
    if state.get("step", 0) < 0:
        state["step"] = 0
        print("WARNING: Reset negative step counter")
    
    # Truncate oversized data
    if len(state.get("conversation_history", [])) > 50:
        state["conversation_history"] = state["conversation_history"][-50:]
        print("INFO: Truncated conversation history to last 50 messages")
    
    return state

def safe_node_transition(state):
    """Safely transition between nodes with state validation"""
    try:
        # Validate state before processing
        state = validate_and_fix_state(state)
        
        # Your node logic here
        result = process_node(state)
        
        # Validate state after processing
        return validate_and_fix_state(result)
        
    except Exception as e:
        print(f"ERROR in node transition: {e}")
        # Return a safe fallback state
        return {
            "user_query": state.get("user_query", "[ERROR]"),
            "step": state.get("step", 0),
            "error": str(e),
            "status": "recovered"
        }
```

#### State Recovery Strategies

1. **Missing Keys**: Provide sensible defaults
2. **Wrong Types**: Convert or reset to expected type
3. **Corrupted Data**: Truncate or clear problematic fields
4. **Oversized State**: Implement size limits and cleanup
5. **Invalid Values**: Apply bounds checking and correction

### Benefits
- Prevents mysterious crashes from state corruption
- Enables graceful recovery from data inconsistencies
- Provides clear logging for debugging issues
- Maintains system stability even with malformed state

> 💡 **Key Insight**: Defensive programming is your friend. Assume state can be corrupted and design for recovery.

---

## Iteration Caps and Loop Detection

### Problem
Agents can get stuck in infinite loops or excessive retry cycles, leading to runaway costs, resource exhaustion, and systems that never terminate.

### Solution
Enforce hard limits on iterations and implement loop detection to prevent agents from running indefinitely.

#### Basic Iteration Limiting

In LangGraph, track iteration count in the agent state:

```python
def should_continue(state):
    max_iterations = 10
    state["iteration"] = state.get("iteration", 0) + 1
    return state["iteration"] <= max_iterations

def conditional_router(state):
    if not should_continue(state):
        return "fallback_summary"  # Exit to fallback
    return "continue_processing"   # Continue normal flow
```

#### Advanced Loop Detection

```python
import hashlib
from collections import deque

class LoopDetector:
    def __init__(self, max_iterations=10, history_size=5):
        self.max_iterations = max_iterations
        self.state_history = deque(maxlen=history_size)
        self.iteration_count = 0
    
    def check_loop(self, state):
        self.iteration_count += 1
        
        # Check iteration limit
        if self.iteration_count > self.max_iterations:
            return "max_iterations_exceeded"
        
        # Create state fingerprint
        state_key = self._create_state_fingerprint(state)
        
        # Check for repeated states (loop detection)
        if state_key in self.state_history:
            return "loop_detected"
        
        self.state_history.append(state_key)
        return "continue"
    
    def _create_state_fingerprint(self, state):
        """Create a hash of relevant state components"""
        relevant_data = {
            "query": state.get("user_query", ""),
            "step": state.get("current_step", ""),
            "last_action": state.get("last_action", "")
        }
        return hashlib.md5(str(relevant_data).encode()).hexdigest()

# Usage in LangGraph node
def process_with_loop_detection(state):
    detector = state.get("loop_detector", LoopDetector())
    state["loop_detector"] = detector
    
    loop_status = detector.check_loop(state)
    
    if loop_status == "max_iterations_exceeded":
        return {
            **state,
            "status": "terminated",
            "reason": "Maximum iterations exceeded",
            "next": "fallback_summary"
        }
    elif loop_status == "loop_detected":
        return {
            **state,
            "status": "terminated", 
            "reason": "Infinite loop detected",
            "next": "fallback_summary"
        }
    
    # Continue normal processing
    return process_node_logic(state)
```

#### Graceful Termination Strategies

```python
def create_fallback_summary(state):
    """Generate a helpful response when loops are detected"""
    iteration_count = state.get("iteration", 0)
    
    if iteration_count > 10:
        message = "I've been working on this for a while but haven't found a complete solution. Here's what I've discovered so far..."
    else:
        message = "I detected I was repeating the same steps. Let me summarize what I found..."
    
    return {
        **state,
        "final_response": message + generate_partial_summary(state),
        "status": "completed_with_fallback"
    }
```

### What This Solves

✅ **Infinite loops** in LangGraph workflows  
✅ **Excessive reasoning cycles** that never converge  
✅ **Runaway token usage** from looped LLM/tool calls  
✅ **Stalled systems** with no exit condition  
✅ **Resource exhaustion** from unbounded execution  

### Best Practices

1. **Set reasonable limits**: 10-20 iterations for most workflows
2. **Log loop events**: Track when and why loops occur
3. **Provide user feedback**: Explain what happened and what was found
4. **Monitor costs**: Set up alerts before expenses spiral
5. **Test edge cases**: Verify loop detection works with your specific workflows

> 💡 **Key Insight**: Add debug logs inside loops to catch repetition early and set up alerts before costs spiral.

---

## Exponential Backoff and Retry Logic

### Problem
LLM timeouts, API failures, and rate-limiting can cause temporary service disruptions. Simple retries without delays can overwhelm failing services and make problems worse.

### Solution
Implement exponential backoff that increases wait times between retry attempts, giving services time to recover while avoiding thundering herd problems.

#### Basic Retry with Exponential Backoff

```python
import time
import random

def call_with_retry(func, max_retries=3, base_delay=2, max_delay=60):
    """
    Retry a function with exponential backoff and jitter
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
    """
for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            jitter = random.uniform(0.1, 0.3) * delay
            total_delay = delay + jitter
            
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.2f}s...")
            time.sleep(total_delay)

# Usage examples
def call_llm():
    return model.invoke(prompt, timeout=30)

def call_api():
    return requests.get(api_url, timeout=10)

# Retry LLM calls
response = call_with_retry(call_llm, max_retries=3, base_delay=1)

# Retry API calls with longer delays
api_data = call_with_retry(call_api, max_retries=5, base_delay=2)
```

#### Advanced Retry with Different Exception Handling

```python
from functools import wraps
import logging

def retry_with_backoff(max_retries=3, base_delay=1, backoff_factor=2, 
                      retryable_exceptions=(Exception,)):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay (2 = double each time)
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
                        logging.error(f"Function {func.__name__} failed after {max_retries} retries")
                        raise e
                    
                    delay = base_delay * (backoff_factor ** attempt)
                    jitter = random.uniform(0.8, 1.2) * delay
                    
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {jitter:.2f}s")
                    time.sleep(jitter)
                except Exception as e:
                    # Non-retryable exception, fail immediately
                    logging.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise e
            
            raise last_exception
        return wrapper
    return decorator

# Usage with decorator
@retry_with_backoff(max_retries=3, base_delay=1, 
                   retryable_exceptions=(requests.RequestException, TimeoutError))
def fetch_weather_data(city):
    response = requests.get(f"https://api.weather.com/v1/current?q={city}", timeout=10)
    response.raise_for_status()
    return response.json()
```

#### Retry Strategies by Error Type

```python
def smart_retry(func, max_retries=3):
    """Adjust retry behavior based on error type"""
    for attempt in range(max_retries + 1):
        try:
return func()
        except requests.exceptions.Timeout:
            # Network timeouts - retry with longer delays
            delay = 5 * (2 ** attempt)
        except requests.exceptions.ConnectionError:
            # Connection issues - retry quickly
            delay = 1 * (2 ** attempt)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                delay = 10 * (2 ** attempt)  # Longer delays for rate limits
            elif e.response.status_code >= 500:  # Server errors
                delay = 3 * (2 ** attempt)
            else:
                # Client errors (4xx) - don't retry
                raise e
        except Exception as e:
            if attempt == max_retries:
                raise e
            delay = 2 * (2 ** attempt)
        
        if attempt < max_retries:
            time.sleep(min(delay, 60))  # Cap at 60 seconds
```

### When to Use Retries

✅ **Safe to retry:**
- Network timeouts
- Rate limiting (429 errors)
- Server errors (5xx)
- Temporary service unavailability
- Transient database connection issues

❌ **Don't retry:**
- Authentication errors (401, 403)
- Bad requests (400)
- Not found errors (404)
- Operations with side effects (payments, data mutations)
- Validation errors

### Benefits
- Recovers from transient failures automatically
- Reduces user-facing errors from temporary issues
- Prevents overwhelming failing services
- Provides graceful degradation during outages

> 💡 **Key Insight**: Only retry safe, repeatable actions. Don't retry operations that cause side effects or change state.

---

## Resource Usage Limits and Tool Sandboxing

### Problem
Some tools can consume excessive resources — spawn subprocesses, load huge files, flood the network, or consume unlimited memory. Even simple Python tools can become dangerous without proper limits.

### Solution
Set explicit bounds around resource usage and implement sandboxing for potentially dangerous operations.

#### Resource Limiting Examples

```python
import psutil
import signal
import time
from functools import wraps

def resource_limited(max_memory_mb=500, max_time_seconds=30, max_file_size_mb=10):
    """Decorator to limit resource usage of functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} exceeded {max_time_seconds}s limit")
            
            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max_time_seconds)
            
            try:
                result = func(*args, **kwargs)
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_used = current_memory - initial_memory
                
                if memory_used > max_memory_mb:
                    raise MemoryError(f"Function {func.__name__} used {memory_used:.1f}MB, limit is {max_memory_mb}MB")
                
                return result
            finally:
                signal.alarm(0)  # Cancel timeout
        
        return wrapper
    return decorator

# Usage
@resource_limited(max_memory_mb=100, max_time_seconds=10)
def process_large_document(document):
    # Your processing logic here
    chunks = document.split('\n\n')
    
    # Limit chunk count
if len(chunks) > 100:
        raise ValueError("Too many chunks to process (limit: 100)")
    
    return analyze_chunks(chunks)
```

#### File Size and Content Limits

```python
def safe_file_processor(file_path, max_size_mb=50):
    """Safely process files with size limits"""
    import os
    
    # Check file size before processing
    file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
    if file_size > max_size_mb:
        raise ValueError(f"File too large: {file_size:.1f}MB (limit: {max_size_mb}MB)")
    
    # Process in chunks to limit memory usage
    chunk_size = 1024 * 1024  # 1MB chunks
    processed_data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            processed_data.append(process_chunk(chunk))
    
    return processed_data

def limit_api_calls(max_concurrent=5, max_per_minute=60):
    """Limit concurrent API calls and rate"""
    import threading
    from collections import deque
    
    semaphore = threading.Semaphore(max_concurrent)
    call_times = deque()
    lock = threading.Lock()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Rate limiting
            with lock:
                now = time.time()
                # Remove calls older than 1 minute
                while call_times and call_times[0] < now - 60:
                    call_times.popleft()
                
                if len(call_times) >= max_per_minute:
                    raise Exception(f"Rate limit exceeded: {max_per_minute} calls per minute")
                
                call_times.append(now)
            
            # Concurrency limiting
            with semaphore:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

#### Container-Based Sandboxing

```python
import subprocess
import json
import tempfile

def run_in_sandbox(code, timeout=30):
    """Run potentially dangerous code in a Docker container"""
    
    # Create temporary file with code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Run in restricted Docker container
        cmd = [
            'docker', 'run', '--rm',
            '--memory=128m',           # Limit memory
            '--cpus=0.5',             # Limit CPU
            '--network=none',         # No network access
            '--read-only',            # Read-only filesystem
            '-v', f'{temp_file}:/app/code.py:ro',  # Mount code read-only
            'python:3.9-alpine',
            'timeout', str(timeout),   # Time limit
            'python', '/app/code.py'
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout + 5  # Extra buffer
        )
        
        if result.returncode != 0:
            raise Exception(f"Sandboxed execution failed: {result.stderr}")
        
        return result.stdout
        
    finally:
        os.unlink(temp_file)  # Clean up
```

### Resource Limits to Implement

1. **Memory Usage**: Set maximum RAM per operation
2. **Execution Time**: Timeout long-running operations  
3. **File Sizes**: Limit document and data file sizes
4. **Network Calls**: Rate limit and concurrent request limits
5. **Disk Usage**: Prevent excessive temporary file creation
6. **CPU Usage**: Limit processing-intensive operations

### Sandboxing Strategies

- **Process isolation**: Run risky code in separate processes
- **Container sandboxing**: Use Docker for complete isolation
- **Resource quotas**: Set system-level limits (ulimit, cgroups)
- **Permission restrictions**: Run with minimal privileges
- **Network isolation**: Disable network access for untrusted code

### Benefits
- Prevents resource exhaustion attacks
- Protects system stability from runaway processes
- Enables safe execution of user-provided code
- Maintains performance under load
- Provides predictable resource usage

> 💡 **Key Insight**: In shared or production environments, always assume tools can be misused and set appropriate boundaries.

---

## Best Practices Summary

### The Defensive Mindset
Building robust AI agents requires adopting a **defensive programming mindset**:

1. **Assume failure**: Every component can and will fail
2. **Plan for recovery**: Design fallback strategies for each failure mode
3. **Validate everything**: Never trust input, output, or state without verification
4. **Set boundaries**: Implement limits on resources, iterations, and execution time
5. **Monitor actively**: Log events, track metrics, and set up alerts

### Implementation Checklist

✅ **Output Validation**
- [ ] Pydantic models with custom validators
- [ ] Fallback values for missing/invalid data
- [ ] Structured output enforcement

✅ **Failure Handling**
- [ ] Circuit breakers for external services
- [ ] Exponential backoff for retries
- [ ] Fallback data sources

✅ **State Management**
- [ ] State validation before each node
- [ ] Recovery strategies for corrupted state
- [ ] Default values for missing keys

✅ **Loop Prevention**
- [ ] Iteration counters and limits
- [ ] Loop detection algorithms
- [ ] Graceful termination strategies

✅ **Resource Protection**
- [ ] Memory and time limits
- [ ] File size restrictions
- [ ] Rate limiting for API calls
- [ ] Sandboxing for risky operations

### Remember
> **The goal isn't to prevent all failures — it's to fail gracefully and recover quickly.**

Production AI systems that implement these patterns will be more reliable, maintainable, and cost-effective than those that don't. Start with the patterns most relevant to your use case, then gradually add more defensive measures as your system matures.