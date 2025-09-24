"""
Defensive State Management for VacayMate

Enhanced state management with defensive programming patterns:
- State validation and recovery
- Safe state transitions
- Loop detection integration
- Comprehensive error handling
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Import defensive patterns
from defensive_patterns import (
    validate_and_fix_state,
    safe_state_transition,
    with_loop_detection,
    LoopDetector
)

# Import original state definitions
from states.VacayMate_state import VacationPlannerState, initialize_vacation_state

class DefensiveStateManager:
    """
    Enhanced state manager with defensive programming patterns.
    
    This class provides safe state operations with:
    - Automatic validation and repair
    - Loop detection
    - Error recovery
    - State history tracking
    """
    
    def __init__(self, max_iterations: int = 15, enable_history: bool = True):
        self.max_iterations = max_iterations
        self.enable_history = enable_history
        self.state_history: List[Dict[str, Any]] = []
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.created_at = datetime.now()
    
    def create_safe_state(self, **kwargs) -> VacationPlannerState:
        """
        Create a new state with defensive validation.
        
        Args:
            **kwargs: State initialization parameters
            
        Returns:
            VacationPlannerState: Validated and safe state
        """
        # Create initial state using original function
        state = initialize_vacation_state(**kwargs)
        
        # Apply defensive validation
        state = validate_and_fix_state(state)
        
        # Add defensive metadata
        state.update({
            "_created_at": datetime.now().isoformat(),
            "_state_version": 1,
            "_error_count": 0,
            "_last_validation": datetime.now().isoformat(),
            "_loop_detector": LoopDetector(max_iterations=self.max_iterations)
        })
        
        # Store in history if enabled
        if self.enable_history:
            self.state_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "create",
                "state_snapshot": self._create_state_snapshot(state)
            })
        
        return state
    
    def validate_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and repair state with comprehensive checks.
        
        Args:
            state: Current state dictionary
            
        Returns:
            Dict: Validated and repaired state
        """
        try:
            # Apply basic validation
            state = validate_and_fix_state(state)
            
            # Update validation metadata
            state["_last_validation"] = datetime.now().isoformat()
            state["_state_version"] = state.get("_state_version", 1) + 1
            
            # Validate specific VacayMate requirements
            state = self._validate_vacaymate_specifics(state)
            
            # Store validation in history
            if self.enable_history:
                self.state_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "validate",
                    "state_snapshot": self._create_state_snapshot(state)
                })
            
            return state
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            
            # Return a minimal safe state if validation fails completely
            return self._create_emergency_state(state, str(e))
    
    def _validate_vacaymate_specifics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VacayMate-specific state requirements."""
        
        # Ensure travel dates are consistent
        start_date = state.get("start_date", "")
        return_date = state.get("return_date", "")
        
        if start_date and return_date:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
                
                if start >= end:
                    state["return_date"] = (start + timedelta(days=7)).isoformat()
                    print("Warning: Fixed invalid date range in state")
                    
            except ValueError:
                # If date parsing fails, set reasonable defaults
                today = datetime.now()
                state["start_date"] = today.isoformat()
                state["return_date"] = (today + timedelta(days=7)).isoformat()
                print("Warning: Fixed invalid date format in state")
        
        # Validate location fields
        for location_field in ["current_location", "destination"]:
            location = state.get(location_field, "")
            if not location or location == "[MISSING]":
                state[location_field] = "Unknown Location"
                print(f"Warning: Fixed missing {location_field} in state")
        
        # Ensure results dictionaries have proper structure
        for result_key in ["research_results", "calculator_results", "planner_results"]:
            if result_key not in state:
                state[result_key] = {}
            elif not isinstance(state[result_key], dict):
                state[result_key] = {}
                print(f"Warning: Fixed invalid {result_key} type in state")
        
        # Validate message lists length and content
        max_messages = 100
        for msg_key in ["manager_messages", "researcher_messages", "calculator_messages", 
                       "planner_messages", "summarizer_messages"]:
            messages = state.get(msg_key, [])
            if not isinstance(messages, list):
                state[msg_key] = []
                print(f"Warning: Fixed invalid {msg_key} type in state")
            elif len(messages) > max_messages:
                state[msg_key] = messages[-max_messages:]
                print(f"Warning: Truncated {msg_key} to {max_messages} messages")
        
        return state
    
    def _create_emergency_state(self, original_state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create a minimal emergency state when validation fails completely."""
        emergency_state = {
            "user_request": original_state.get("user_request", "[EMERGENCY_STATE]"),
            "current_location": original_state.get("current_location", "Unknown"),
            "destination": original_state.get("destination", "Unknown"),
            "start_date": datetime.now().isoformat(),
            "return_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "travel_dates": "Emergency state - dates reset",
            "manager_messages": [],
            "researcher_messages": [],
            "calculator_messages": [],
            "planner_messages": [],
            "summarizer_messages": [],
            "research_results": {},
            "calculator_results": {},
            "planner_results": {},
            "manager_prompt": {},
            "researcher_prompt": {},
            "calculator_prompt": {},
            "planner_prompt": {},
            "summarizer_prompt": {},
            "tools": [],
            "itinerary_draft": "",
            "final_plan": f"Emergency state created due to validation error: {error}",
            "plan_approved": False,
            "_emergency_state": True,
            "_emergency_reason": error,
            "_emergency_created": datetime.now().isoformat(),
            "_state_version": 0,
            "_error_count": self.error_count
        }
        
        print(f"EMERGENCY: Created emergency state due to: {error}")
        return emergency_state
    
    def _create_state_snapshot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lightweight snapshot of state for history tracking."""
        return {
            "user_request": state.get("user_request", ""),
            "destination": state.get("destination", ""),
            "current_location": state.get("current_location", ""),
            "message_counts": {
                "manager": len(state.get("manager_messages", [])),
                "researcher": len(state.get("researcher_messages", [])),
                "calculator": len(state.get("calculator_messages", [])),
                "planner": len(state.get("planner_messages", [])),
                "summarizer": len(state.get("summarizer_messages", []))
            },
            "has_results": {
                "research": bool(state.get("research_results")),
                "calculator": bool(state.get("calculator_results")),
                "planner": bool(state.get("planner_results"))
            },
            "plan_approved": state.get("plan_approved", False),
            "state_version": state.get("_state_version", 0),
            "error_count": state.get("_error_count", 0)
        }
    
    def get_state_health(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive health information about the current state."""
        loop_detector = state.get("_loop_detector")
        loop_stats = loop_detector.get_stats() if loop_detector else {}
        
        return {
            "state_version": state.get("_state_version", 0),
            "error_count": state.get("_error_count", 0),
            "last_validation": state.get("_last_validation"),
            "created_at": state.get("_created_at"),
            "is_emergency_state": state.get("_emergency_state", False),
            "emergency_reason": state.get("_emergency_reason"),
            "loop_detection": loop_stats,
            "message_counts": {
                key: len(state.get(key, []))
                for key in ["manager_messages", "researcher_messages", 
                           "calculator_messages", "planner_messages", "summarizer_messages"]
            },
            "has_required_fields": {
                "user_request": bool(state.get("user_request")),
                "destination": bool(state.get("destination")),
                "current_location": bool(state.get("current_location")),
                "dates": bool(state.get("start_date") and state.get("return_date"))
            },
            "results_available": {
                "research": bool(state.get("research_results")),
                "calculator": bool(state.get("calculator_results")),
                "planner": bool(state.get("planner_results"))
            },
            "manager_stats": {
                "total_history_entries": len(self.state_history),
                "total_errors": self.error_count,
                "last_error": self.last_error
            }
        }
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get the complete state history."""
        return self.state_history.copy()
    
    def clear_history(self):
        """Clear the state history (useful for memory management)."""
        self.state_history.clear()

# Global defensive state manager instance
defensive_state_manager = DefensiveStateManager()

# Enhanced initialization function with defensive patterns
def initialize_defensive_vacation_state(**kwargs) -> VacationPlannerState:
    """
    Initialize a vacation state with defensive patterns applied.
    
    This function creates a state that is:
    - Validated and error-corrected
    - Protected against common failure modes
    - Enhanced with loop detection
    - Tracked for debugging and monitoring
    
    Args:
        **kwargs: Same arguments as original initialize_vacation_state
        
    Returns:
        VacationPlannerState: Enhanced defensive state
    """
    return defensive_state_manager.create_safe_state(**kwargs)

# Decorator for safe node operations
def defensive_node(max_iterations: int = 15):
    """
    Decorator to make node functions defensive.
    
    This decorator adds:
    - State validation before and after processing
    - Loop detection
    - Error recovery
    - Comprehensive logging
    
    Args:
        max_iterations: Maximum iterations before terminating
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @with_loop_detection(max_iterations=max_iterations)
        @safe_state_transition
        def wrapper(state: Dict[str, Any], *args, **kwargs):
            # Validate state before processing
            state = defensive_state_manager.validate_state(state)
            
            # Add processing metadata
            state["_last_node"] = func.__name__
            state["_last_node_time"] = datetime.now().isoformat()
            
            try:
                # Execute the original function
                result = func(state, *args, **kwargs)
                
                # Validate result state
                if isinstance(result, dict):
                    result = defensive_state_manager.validate_state(result)
                    result["_last_successful_node"] = func.__name__
                    result["_last_success_time"] = datetime.now().isoformat()
                
                return result
                
            except Exception as e:
                # Handle node-specific errors
                error_msg = f"Error in node {func.__name__}: {str(e)}"
                print(f"DEFENSIVE NODE ERROR: {error_msg}")
                
                # Update error tracking
                state["_error_count"] = state.get("_error_count", 0) + 1
                state["_last_error"] = error_msg
                state["_last_error_time"] = datetime.now().isoformat()
                state["_last_error_node"] = func.__name__
                
                # Return state with error information
                return defensive_state_manager.validate_state(state)
        
        return wrapper
    return decorator

# Test functions
def test_defensive_state():
    """Test the defensive state management functionality."""
    print("Testing defensive state management...")
    
    # Test normal state creation
    state = initialize_defensive_vacation_state(
        user_request="Test trip",
        current_location="Paris",
        destination="London",
        start_date="2025-10-15",
        return_date="2025-10-22"
    )
    
    print("✅ Created defensive state")
    print(f"State health: {defensive_state_manager.get_state_health(state)}")
    
    # Test state corruption and recovery
    corrupted_state = state.copy()
    corrupted_state["manager_messages"] = "invalid_type"  # Should be list
    corrupted_state["start_date"] = "invalid_date"
    del corrupted_state["destination"]  # Remove required field
    
    print("\n Testing state recovery...")
    recovered_state = defensive_state_manager.validate_state(corrupted_state)
    print("✅ State recovered from corruption")
    print(f"Recovered state health: {defensive_state_manager.get_state_health(recovered_state)}")
    
    # Test emergency state creation
    print("\n Testing emergency state creation...")
    try:
        # Simulate complete validation failure
        completely_broken_state = {"invalid": "state"}
        emergency_state = defensive_state_manager._create_emergency_state(
            completely_broken_state, "Complete state corruption"
        )
        print("✅ Emergency state created successfully")
        print(f"Emergency state health: {defensive_state_manager.get_state_health(emergency_state)}")
    except Exception as e:
        print(f"❌ Emergency state creation failed: {e}")

if __name__ == "__main__":
    test_defensive_state()

