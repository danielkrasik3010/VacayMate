# VacayMate Test Suite

## Overview

This comprehensive test suite provides robust unit testing for My VacayMate AI travel planning system. The tests focus on deterministic components while properly mocking non-deterministic external dependencies like API calls and LLM interactions.

## Test Architecture

### Test Categories

1. **Unit Tests** - Test individual functions and components in isolation
2. **Integration Tests** - Test component interactions and data flow
3. **Edge Case Tests** - Test boundary conditions and error scenarios
4. **Mock Tests** - Test with simulated API responses and data

### Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test configuration
├── fixtures/                   # Mock data files
│   ├── mock_flights.json      # Flight API response samples
│   ├── mock_hotels.json       # Hotel API response samples
│   └── mock_events.json       # Event API response samples
├── test_tools.py              # Tool functionality tests
├── test_city_validation       # city validation tests   
├── test_calculator.py         # Cost calculation tests
├── test_formatters.py         # Markdown/export formatting tests
├── test_states.py             # State management tests
├── test_edge_cases.py         # Edge cases and error handling
└── README.md                  # This file
```

## Running Tests

### Prerequisites

Install testing dependencies:
```bash
pip install -r requirements.txt
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_tools.py
```

Run tests in parallel:
```bash
pytest -n auto
```

### Test Markers

Tests are organized with markers for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only edge case tests  
pytest -m edge_case

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Verbose Output

For detailed test output:
```bash
pytest -v
```

For extra verbose output with print statements:
```bash
pytest -v -s
```

## Test Files Description

### `conftest.py`
- **Purpose**: Central configuration and shared fixtures
- **Contains**: Mock data loaders, API client mocks, state fixtures, helper functions
- **Key Fixtures**: `mock_flight_data`, `mock_hotel_data`, `sample_vacation_state`, `populated_vacation_state`

### `test_tools.py`
- **Purpose**: Test tool functionality and data processing
- **Coverage**: Flight/hotel parsers, quotation calculations, city mapping, data validation
- **Focus**: Deterministic functions only, API calls are mocked
- **Key Tests**: Price parsing, duration calculations, address formatting

### `test_calculator.py`
- **Purpose**: Test financial calculations and cost aggregations
- **Coverage**: Cost totaling, commission calculations, price averaging, currency handling
- **Focus**: Mathematical accuracy, rounding behavior, edge cases
- **Key Tests**: Quotation accuracy, commission rates, extreme values

### `test_formatters.py`
- **Purpose**: Test markdown generation and data export
- **Coverage**: Table formatting, attraction parsing, file export, content generation
- **Focus**: Output formatting, data structure conversion, file operations
- **Key Tests**: Markdown structure, table generation, special character handling

### `test_states.py`
- **Purpose**: Test state management and transitions
- **Coverage**: State initialization, updates, validation, Pydantic models
- **Focus**: Data integrity, type validation, state consistency
- **Key Tests**: State structure, field validation, concurrent updates

### `test_edge_cases.py`
- **Purpose**: Test boundary conditions and error scenarios
- **Coverage**: Missing data, extreme values, corrupted input, error handling
- **Focus**: System robustness, graceful degradation, error recovery
- **Key Tests**: Empty data handling, invalid inputs, memory limits

## Mock Data

### Flight Data (`fixtures/mock_flights.json`)
- Sample flight itineraries with complete booking details
- Edge cases: empty data, malformed entries, extreme prices
- Multiple airlines, routes, and price points

### Hotel Data (`fixtures/mock_hotels.json`)  
- Hotel listings with pricing, ratings, and location data
- Edge cases: missing fields, invalid coordinates, price variations
- Different hotel classes and amenities

### Event Data (`fixtures/mock_events.json`)
- Local events with dates, venues, and descriptions
- Edge cases: null values, special characters, long descriptions
- Various event types and ticket information

## Mocking Strategy

### API Mocking
- **Groq Client**: Mock LLM responses for daily cost estimation
- **SerpAPI**: Mock hotel and event search results
- **OpenWeatherMap**: Mock weather forecast data  
- **Tavily**: Mock destination research content
- **RapidAPI**: Mock flight price data

### Environment Variables
- All API keys are automatically mocked in test environment
- No real API calls are made during testing
- Environment isolation prevents accidental live API usage

### File System Mocking
- Export operations use temporary directories
- File write operations are mocked to prevent filesystem pollution
- Error conditions (permissions, disk space) are simulated

## Test Coverage

### Deterministic Components (100% Coverage Goal)
- ✅ Price calculations and aggregations
- ✅ Date arithmetic and formatting
- ✅ Data parsing and validation
- ✅ Markdown generation and export
- ✅ State initialization and updates
- ✅ Currency formatting and rounding

### Mocked Components (Interface Testing)
- ✅ API client interfaces
- ✅ LLM integration points
- ✅ File system operations
- ✅ Network error handling
- ✅ External service timeouts

### Edge Cases (Comprehensive Coverage)
- ✅ Empty and null data handling
- ✅ Extreme values and boundary conditions
- ✅ Malformed input data
- ✅ Memory and performance limits
- ✅ Concurrent operation scenarios
- ✅ Error propagation and recovery


## Performance Considerations

### Test Execution Speed
- **Fast Tests**: Unit tests run in <5 seconds for each one
- **Parallel Execution**: Use `pytest-xdist` for parallel test runs
- **Selective Testing**: Use markers to run specific test subsets
- **Mock Efficiency**: All external calls are mocked for speed

### Memory Usage
- **Fixture Reuse**: Shared fixtures minimize memory overhead
- **Data Cleanup**: Temporary data is automatically cleaned up
- **Large Data Tests**: Edge case tests handle large datasets efficiently

## Debugging Tests

### Common Issues
1. **Import Errors**: Ensure `PYTHONPATH` includes project root
2. **Mock Failures**: Check that API clients are properly mocked
3. **Fixture Issues**: Verify fixture dependencies and scoping
4. **Environment Variables**: Confirm test environment isolation


### Logging
Tests include comprehensive logging for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### some guidelines if you want to add new Tests
1. **Follow Naming Convention**: `test_*.py` files, `test_*` functions
2. **Use Appropriate Fixtures**: Reuse existing fixtures when possible
3. **Mock External Dependencies**: Dont make real API calls (to not waste tokens)
4. **Include Edge Cases**: Test boundary conditions and error scenarios
5. **Document Complex Tests**: Add docstrings explaining test purpose

### Test Quality Guidelines
- **Single Responsibility**: Each test should verify one specific behavior
- **Clear Assertions**: Use descriptive assertion messages
- **Proper Setup/Teardown**: Use fixtures for test data setup
- **Independence**: Tests should not depend on execution order
- **Deterministic**: Tests should produce consistent results

### Code Coverage Goals
- **Minimum Coverage**: 80% overall code coverage
- **Critical Components**: 95%+ coverage for calculation logic
- **New Features**: 100% coverage required for new functionality
- **Edge Cases**: Comprehensive coverage of error conditions

## Troubleshooting

### Common Test Failures

1. **ModuleNotFoundError**
   ```bash
   # Solution: Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Mock Assertion Errors**
   ```python
   # Check mock call arguments
   mock_function.assert_called_with(expected_args)
   ```

3. **Fixture Scope Issues**
   ```python
   # Use appropriate fixture scope
   @pytest.fixture(scope="function")  # or "session", "module"
   ```


### Getting Help
- Check test logs for detailed error information
- Use `pytest --tb=long` for full tracebacks
- Review fixture definitions in `conftest.py`
- Consult individual test file docstrings

## Metrics and Reporting

### Coverage Reports
Generate detailed coverage reports:
```bash
pytest --cov=code --cov-report=html --cov-report=term --cov-report=xml
```

## Future Enhancements

### Planned Improvements
- [ ] Integration tests with real API sandboxes
- [ ] Performance benchmarking tests
- [ ] Property-based testing with Hypothesis
- [ ] Visual regression tests for UI components
- [ ] Load testing for concurrent operations

### Monitoring
- [ ] Test execution time tracking
- [ ] Coverage trend analysis  
- [ ] Flaky test detection
- [ ] Test result analytics dashboard

---

**Last Updated**: October 2025  
**Maintainer**: VacayMate Development Team ( Daniel Krasik HAHA) 
**Version**: 1.0.0
