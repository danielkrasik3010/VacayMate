"""
Defensive VacayMate System

Enhanced version of the VacayMate system with comprehensive defensive programming patterns:
- Circuit breaker protection for all external APIs
- State validation and recovery
- Loop detection and iteration limits
- Exponential backoff retry logic
- Resource usage monitoring
- Comprehensive error handling and logging
"""

import sys
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import defensive patterns and components
from defensive_patterns import (
    circuit_breaker,
    get_system_health,
    ValidatedFlightResponse,
    ValidatedHotelResponse,
    ValidatedWeatherResponse
)

from states.defensive_state import (
    initialize_defensive_vacation_state,
    defensive_state_manager,
    DefensiveStateManager
)

from nodes.defensive_nodes import (
    make_defensive_manager_node,
    make_defensive_researcher_node,
    make_defensive_calculator_node,
    make_defensive_planner_node,
    make_defensive_summarizer_node,
    make_defensive_merge_node
)

# Import original components for compatibility
from tools.city_mapping import is_valid_city, get_city_validation_error
from graphs.VacayMate_graph import build_vacation_graph
from consts import (
    MANAGER,
    RESEARCHER,
    CALCULATOR,
    PLANNER,
    SUMMARIZER,
    MERGE_RESULTS,
)

# Import configuration utilities
import importlib.util
utils_file_path = os.path.join(os.path.dirname(__file__), 'utils.py')
spec = importlib.util.spec_from_file_location("utils_file", utils_file_path)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)
load_config = utils_module.load_config

class DefensiveVacayMate:
    """
    Enhanced VacayMate system with comprehensive defensive programming patterns.
    
    This system provides:
    - Automatic error recovery and fallback strategies
    - Circuit breaker protection for external APIs
    - State validation and corruption recovery
    - Loop detection and iteration limits
    - Resource usage monitoring
    - Comprehensive logging and health monitoring
    """
    
    def __init__(self, llm_model: str = None, max_iterations: int = 20, 
                 enable_monitoring: bool = True):
        """
        Initialize the defensive VacayMate system.
        
        Args:
            llm_model: LLM model to use (defaults to config value)
            max_iterations: Maximum iterations before terminating (default: 20)
            enable_monitoring: Enable system health monitoring (default: True)
        """
        self.max_iterations = max_iterations
        self.enable_monitoring = enable_monitoring
        self.start_time = time.time()
        self.execution_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "average_runtime": 0.0,
            "last_run_time": None
        }
        
        # Load configuration with fallback
        try:
            self.config = load_config()
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading config: {e}, using fallback configuration")
            self.config = self._get_fallback_config()
        
        # Initialize state manager
        self.state_manager = DefensiveStateManager(
            max_iterations=max_iterations,
            enable_history=enable_monitoring
        )
        
        # Build the defensive graph
        self.graph = self._build_defensive_graph(llm_model)
        
        print(f"🛡️ Defensive VacayMate system initialized with max_iterations={max_iterations}")
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration when config loading fails."""
        return {
            'vacaymate_system': {
                'max_retries': 3,
                'timeout_seconds': 300,
                'model_config': {
                    'temperature': 0.3,
                    'max_tokens': 4000
                },
                'agents': {
                    'manager': {'llm': 'gpt-4o-mini'},
                    'researcher': {'llm': 'gpt-4o-mini'},
                    'calculator': {'llm': 'gpt-4o-mini'},
                    'planner': {'llm': 'gpt-4o-mini'},
                    'summarizer': {'llm': 'gpt-4o-mini'}
                }
            }
        }
    
    def _build_defensive_graph(self, llm_model: str = None):
        """Build the defensive workflow graph."""
        from langgraph.graph import StateGraph, START, END
        from states.VacayMate_state import VacationPlannerState
        
        # Get configuration
        system_config = self.config.get('vacaymate_system', {})
        agents_config = system_config.get('agents', {})
        
        if llm_model is None:
            llm_model = agents_config.get('manager', {}).get('llm', 'gpt-4o-mini')
        
        # Create the graph
        graph = StateGraph(VacationPlannerState)
        
        # Add defensive nodes
        graph.add_node(MANAGER, make_defensive_manager_node(llm=llm_model))
        graph.add_node(RESEARCHER, make_defensive_researcher_node(llm=llm_model))
        graph.add_node(CALCULATOR, make_defensive_calculator_node(llm=llm_model))
        graph.add_node(PLANNER, make_defensive_planner_node(llm=llm_model))
        graph.add_node(MERGE_RESULTS, make_defensive_merge_node(llm=llm_model))
        graph.add_node(SUMMARIZER, make_defensive_summarizer_node(llm=llm_model))
        
        # Add edges (same flow as original)
        graph.add_edge(START, MANAGER)
        graph.add_edge(MANAGER, RESEARCHER)
        graph.add_edge(RESEARCHER, CALCULATOR)
        graph.add_edge(RESEARCHER, PLANNER)
        graph.add_edge(CALCULATOR, MERGE_RESULTS)
        graph.add_edge(PLANNER, MERGE_RESULTS)
        graph.add_edge(MERGE_RESULTS, SUMMARIZER)
        graph.add_edge(SUMMARIZER, END)
        
        return graph.compile()
    
    def validate_cities(self, current_location: str, destination: str) -> Dict[str, str]:
        """
        Validate departure city and destination with enhanced error handling.
        
        Args:
            current_location: The departure city
            destination: The destination city
            
        Returns:
            Dict containing validation errors, empty if all valid
        """
        errors = {}
        
        try:
            # Validate departure city
            if not is_valid_city(current_location):
                errors['departure_city'] = get_city_validation_error(current_location, "Departure City")
            
            # Validate destination
            if not is_valid_city(destination):
                errors['destination'] = get_city_validation_error(destination, "Destination")
                
        except Exception as e:
            # If city validation itself fails, provide a generic error
            errors['validation_error'] = f"City validation service error: {str(e)}"
        
        return errors
    
    def run(self, user_request: str, current_location: str, destination: str, 
            start_date: str, return_date: str, export_markdown: bool = True) -> Dict[str, Any]:
        """
        Run the defensive VacayMate workflow with comprehensive error handling.
        
        Args:
            user_request: User's travel request
            current_location: Departure city
            destination: Destination city
            start_date: Trip start date (YYYY-MM-DD)
            return_date: Trip return date (YYYY-MM-DD)
            export_markdown: Whether to export results to markdown file
            
        Returns:
            Dict: Final state with comprehensive results and error information
        """
        run_start_time = time.time()
        self.execution_stats["total_runs"] += 1
        
        try:
            print(f"🛡️ Starting defensive VacayMate workflow...")
            print(f"📍 Trip: {current_location} → {destination}")
            print(f"📅 Dates: {start_date} to {return_date}")
            
            # Pre-flight system health check
            if self.enable_monitoring:
                health = get_system_health()
                disabled_services = [name for name, status in health.get("circuit_breakers", {}).items() 
                                   if status.get("disabled", False)]
                if disabled_services:
                    print(f"⚠️ Warning: {len(disabled_services)} services currently disabled: {disabled_services}")
            
            # Validate cities with enhanced error handling
            validation_errors = self.validate_cities(current_location, destination)
            if validation_errors:
                error_messages = []
                for field, error in validation_errors.items():
                    error_messages.append(f"**{field.replace('_', ' ').title()} Error:**\n{error}")
                
                # Create error state instead of raising exception
                error_state = self.state_manager.create_safe_state(
                    user_request=user_request,
                    current_location=current_location,
                    destination=destination,
                    start_date=start_date,
                    return_date=return_date
                )
                
                error_state["final_plan"] = f"❌ **Validation Errors:**\n\n{chr(10).join(error_messages)}"
                error_state["plan_approved"] = False
                error_state["validation_errors"] = validation_errors
                
                self.execution_stats["failed_runs"] += 1
                return error_state
            
            # Create initial defensive state
            initial_state = initialize_defensive_vacation_state(
                user_request=user_request,
                current_location=current_location,
                destination=destination,
                start_date=start_date,
                return_date=return_date
            )
            
            print("✅ Initial state created and validated")
            
            # Run the defensive graph
            print("🚀 Executing defensive workflow...")
            final_state = self.graph.invoke(initial_state)
            
            # Validate final state
            final_state = self.state_manager.validate_state(final_state)
            
            # Add execution metadata
            runtime = time.time() - run_start_time
            final_state["_execution_stats"] = {
                "runtime_seconds": runtime,
                "timestamp": datetime.now().isoformat(),
                "system_health": get_system_health() if self.enable_monitoring else {},
                "state_health": self.state_manager.get_state_health(final_state)
            }
            
            # Export to markdown if requested
            if export_markdown:
                try:
                    self._export_markdown_plan(final_state, destination, start_date, return_date)
                except Exception as e:
                    print(f"⚠️ Markdown export failed: {e}")
                    final_state["export_error"] = str(e)
            
            # Update execution statistics
            self.execution_stats["successful_runs"] += 1
            self.execution_stats["last_run_time"] = runtime
            self.execution_stats["average_runtime"] = (
                (self.execution_stats["average_runtime"] * (self.execution_stats["successful_runs"] - 1) + runtime) 
                / self.execution_stats["successful_runs"]
            )
            
            print(f"✅ Defensive workflow completed successfully in {runtime:.2f}s")
            return final_state
            
        except Exception as e:
            # Handle catastrophic failures
            runtime = time.time() - run_start_time
            error_msg = f"Catastrophic system failure: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Create emergency state
            emergency_state = self.state_manager._create_emergency_state(
                {"user_request": user_request, "current_location": current_location, "destination": destination},
                error_msg
            )
            
            emergency_state["_execution_stats"] = {
                "runtime_seconds": runtime,
                "timestamp": datetime.now().isoformat(),
                "catastrophic_failure": True,
                "error": error_msg
            }
            
            self.execution_stats["failed_runs"] += 1
            return emergency_state
    
    def _export_markdown_plan(self, state: Dict[str, Any], destination: str, 
                             start_date: str, return_date: str):
        """Export the vacation plan to a markdown file with enhanced error handling."""
        try:
            import os
            from datetime import datetime
            
            # Create outputs directory
            outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"defensive_vacation_plan_{destination.lower().replace(' ', '_')}_{timestamp}.md"
            filepath = os.path.join(outputs_dir, filename)
            
            # Build enhanced markdown content
            markdown_content = self._build_enhanced_markdown_content(state, destination, start_date, return_date)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"📄 Enhanced vacation plan exported to: {filepath}")
            
        except Exception as e:
            print(f"❌ Error exporting markdown file: {e}")
            raise e
    
    def _build_enhanced_markdown_content(self, state: Dict[str, Any], destination: str, 
                                       start_date: str, return_date: str) -> str:
        """Build enhanced markdown content with defensive system information."""
        lines = [
            f"# 🛡️ Defensive VacayMate Travel Plan: {destination}",
            f"**Generated on:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"**Travel Dates:** {start_date} to {return_date}",
            f"**System:** Defensive VacayMate v2.0 with Enhanced Error Handling",
            "",
            "---",
            ""
        ]
        
        # System Health Section
        execution_stats = state.get("_execution_stats", {})
        system_health = execution_stats.get("system_health", {})
        
        lines.extend([
            "## 🔧 System Status",
            f"**Generation Time:** {execution_stats.get('runtime_seconds', 0):.2f} seconds",
            f"**System Health:** {'✅ All systems operational' if not any(s.get('disabled', False) for s in system_health.get('circuit_breakers', {}).values()) else '⚠️ Some services degraded'}",
            ""
        ])
        
        # Add circuit breaker status if any are disabled
        circuit_breakers = system_health.get("circuit_breakers", {})
        disabled_services = [name for name, status in circuit_breakers.items() if status.get("disabled", False)]
        if disabled_services:
            lines.extend([
                "### ⚠️ Service Status Alerts",
                f"The following services experienced issues during planning: {', '.join(disabled_services)}",
                "Fallback data was used where necessary. Please verify critical information independently.",
                ""
            ])
        
        # Add the main plan content (reuse original logic but enhanced)
        final_plan = state.get("final_plan", "")
        if final_plan:
            lines.extend([
                "## 📋 Complete Travel Plan",
                "",
                final_plan,
                ""
            ])
        
        # Add detailed results sections
        self._add_detailed_results_sections(lines, state)
        
        # Add system metadata
        lines.extend([
            "---",
            "",
            "## 📊 Generation Metadata",
            f"- **System Version:** Defensive VacayMate v2.0",
            f"- **Generation Time:** {execution_stats.get('runtime_seconds', 0):.2f} seconds",
            f"- **State Validations:** {state.get('_state_version', 0)}",
            f"- **Error Count:** {state.get('_error_count', 0)}",
            f"- **Loop Iterations:** {execution_stats.get('state_health', {}).get('loop_detection', {}).get('iteration_count', 0)}",
            "",
            f"*Generated by Defensive VacayMate AI Travel Planning System*",
            f"*Export completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return "\n".join(lines)
    
    def _add_detailed_results_sections(self, lines: list, state: Dict[str, Any]):
        """Add detailed results sections to the markdown content."""
        # Research Results Detail
        research_results = state.get("research_results", {})
        
        # Flights Detail
        flights = research_results.get("flights", [])
        if flights:
            lines.extend([
                "### ✈️ Detailed Flight Analysis",
                f"Found {len(flights)} flight options with defensive validation:",
                ""
            ])
            for i, flight in enumerate(flights[:3], 1):
                price = flight.get("priceUSD", 0)
                airline = flight.get("airline", "Unknown")
                lines.append(f"{i}. **{airline}** - ${price:.2f} - {flight.get('human_readable_summary', 'Details available')}")
            lines.append("")
        
        # Hotels Detail
        hotels = research_results.get("accommodations", {}).get("hotels", [])
        if hotels:
            lines.extend([
                "### 🏨 Detailed Hotel Analysis",
                f"Found {len(hotels)} hotel options with defensive validation:",
                ""
            ])
            for i, hotel in enumerate(hotels[:3], 1):
                name = hotel.get("name", "Unknown Hotel")
                price = hotel.get("price", {}).get("per_night", "N/A")
                rating = hotel.get("rating", "N/A")
                lines.append(f"{i}. **{name}** - {price}/night - {rating}★")
            lines.append("")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status information."""
        return {
            "system_health": get_system_health(),
            "execution_stats": self.execution_stats,
            "uptime_seconds": time.time() - self.start_time,
            "state_manager_stats": {
                "total_history_entries": len(self.state_manager.state_history),
                "total_errors": self.state_manager.error_count,
                "last_error": self.state_manager.last_error
            },
            "configuration": {
                "max_iterations": self.max_iterations,
                "monitoring_enabled": self.enable_monitoring
            }
        }
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers (useful for testing or recovery)."""
        circuit_breaker.failure_counts.clear()
        circuit_breaker.disabled_until.clear()
        circuit_breaker.last_success.clear()
        print("🔄 All circuit breakers have been reset")
    
    def get_health_report(self) -> str:
        """Get a human-readable health report."""
        status = self.get_system_status()
        
        lines = [
            "🛡️ Defensive VacayMate System Health Report",
            f"⏱️ Uptime: {status['uptime_seconds']:.0f} seconds",
            f"📊 Total Runs: {status['execution_stats']['total_runs']}",
            f"✅ Successful: {status['execution_stats']['successful_runs']}",
            f"❌ Failed: {status['execution_stats']['failed_runs']}",
            f"⚡ Avg Runtime: {status['execution_stats']['average_runtime']:.2f}s",
            ""
        ]
        
        # Circuit breaker status
        cb_status = status['system_health'].get('circuit_breakers', {})
        if cb_status:
            lines.append("🔌 Circuit Breaker Status:")
            for name, info in cb_status.items():
                status_icon = "❌" if info.get('disabled', False) else "✅"
                failures = info.get('failures', 0)
                lines.append(f"  {status_icon} {name}: {failures} failures")
            lines.append("")
        
        return "\n".join(lines)

# Test function
def test_defensive_system():
    """Test the defensive VacayMate system."""
    print("🧪 Testing Defensive VacayMate System...")
    
    # Create system instance
    system = DefensiveVacayMate(max_iterations=15, enable_monitoring=True)
    
    # Test normal operation
    print("\n✅ Testing normal operation...")
    result = system.run(
        user_request="Plan a romantic getaway with good food and culture",
        current_location="New York",
        destination="Paris",
        start_date="2025-10-15",
        return_date="2025-10-22",
        export_markdown=False  # Skip export for testing
    )
    
    print(f"Result status: {'✅ Success' if result.get('plan_approved', False) else '⚠️ Partial/Failed'}")
    print(f"Final plan length: {len(result.get('final_plan', ''))}")
    
    # Test error handling
    print("\n🔧 Testing error handling...")
    error_result = system.run(
        user_request="Test invalid cities",
        current_location="InvalidCity123",
        destination="AnotherInvalidCity456",
        start_date="2025-10-15",
        return_date="2025-10-22",
        export_markdown=False
    )
    
    print(f"Error handling: {'✅ Handled gracefully' if 'validation_errors' in error_result else '❌ Not handled'}")
    
    # Print system health
    print(f"\n{system.get_health_report()}")

if __name__ == "__main__":
    test_defensive_system()

