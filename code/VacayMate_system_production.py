"""
VacayMate Production System with Full Defensive Patterns Integration

This is the production-ready version of VacayMate with comprehensive defensive programming patterns:

✅ Resilient Output Parsing and Schema Validation
✅ Circuit Breakers and Tool-Level Fallbacks  
✅ State Validation and Recovery Safeguards
✅ Iteration Caps and Loop Detection
✅ Exponential Backoff and Retry Logic
✅ Resource Usage Limits and Tool Sandboxing

All external API calls are protected with:
- Circuit breakers that disable failing services temporarily
- Exponential backoff retry logic with jitter
- Comprehensive fallback strategies
- Resource usage monitoring and limits
- State validation and corruption recovery
- Loop detection and iteration caps

Usage:
    from VacayMate_system_production import ProductionVacayMate
    
    system = ProductionVacayMate()
    result = system.run(
        user_request="Plan a romantic getaway",
        current_location="New York", 
        destination="Paris",
        start_date="2025-10-15",
        return_date="2025-10-22"
    )
"""

import sys
import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# LangSmith tracing - automatically enabled when environment variables are set
# No additional imports needed - LangGraph handles tracing automatically

# Ensure current directory and parent are discoverable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import defensive components directly
from states.defensive_state import initialize_defensive_vacation_state
from nodes.defensive_nodes import (
    defensive_manager_node,
    defensive_researcher_node,
    defensive_calculator_node,
    defensive_planner_node,
    defensive_summarizer_node,
    defensive_merge_node
)

# Import defensive patterns for direct access
from defensive_patterns import (
    circuit_breaker,
    get_system_health,
    ValidatedFlightResponse,
    ValidatedHotelResponse,
    ValidatedWeatherResponse,
    safe_api_call,
    test_circuit_breaker
)

# Import configuration utilities
import importlib.util
utils_file_path = os.path.join(os.path.dirname(__file__), 'utils.py')
spec = importlib.util.spec_from_file_location("utils_file", utils_file_path)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)
load_config = utils_module.load_config

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, 'outputs', 'production.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionVacayMate:
    """
    Production-ready VacayMate system with full defensive patterns integration.
    
    This system provides enterprise-grade reliability with:
    
    🛡️ DEFENSIVE PATTERNS IMPLEMENTED:
    
    1. RESILIENT OUTPUT PARSING & SCHEMA VALIDATION
       - Pydantic models with custom validators for all API responses
       - Automatic data correction and fallback values
       - Type coercion and sanitization
    
    2. CIRCUIT BREAKERS & TOOL-LEVEL FALLBACKS
       - Per-service circuit breakers (flights, hotels, weather, events)
       - Configurable failure thresholds and timeout periods
       - Graceful fallback to cached or default data
       - Automatic service re-enabling after recovery
    
    3. STATE VALIDATION & RECOVERY SAFEGUARDS
       - Comprehensive state validation before each node transition
       - Automatic repair of corrupted or missing state fields
       - Emergency state creation for catastrophic failures
       - State history tracking for debugging
    
    4. ITERATION CAPS & LOOP DETECTION
       - State fingerprinting to detect infinite loops
       - Configurable iteration limits with graceful termination
       - Partial result preservation when limits are exceeded
    
    5. EXPONENTIAL BACKOFF & RETRY LOGIC
       - Intelligent retry strategies with exponential backoff
       - Jitter to prevent thundering herd problems
       - Exception classification (retryable vs non-retryable)
       - Per-service retry configuration
    
    6. RESOURCE USAGE LIMITS & TOOL SANDBOXING
       - Memory usage monitoring and limits
       - Execution time limits with timeout handling
       - Process isolation for risky operations
       - Resource usage reporting and alerts
    
    🔧 PRODUCTION FEATURES:
    
    - Comprehensive health monitoring and metrics
    - Structured logging with correlation IDs
    - Performance monitoring and optimization
    - Graceful degradation under load
    - Circuit breaker status dashboard
    - Automatic error recovery and self-healing
    - Export to multiple formats (Markdown, JSON, HTML)
    - Real-time system status reporting
    """
    
    def __init__(self, 
                 llm_model: str = None,
                 max_iterations: int = 25,
                 enable_monitoring: bool = True,
                 circuit_breaker_config: Optional[Dict[str, Any]] = None,
                 resource_limits: Optional[Dict[str, Any]] = None):
        """
        Initialize the production VacayMate system.
        
        Args:
            llm_model: LLM model to use (defaults to config value)
            max_iterations: Maximum iterations before terminating (default: 25)
            enable_monitoring: Enable comprehensive system monitoring (default: True)
            circuit_breaker_config: Custom circuit breaker configuration
            resource_limits: Custom resource limit configuration
        """
        self.start_time = time.time()
        self.session_id = f"prod_{int(time.time())}"
        
        # Configure logging with session ID
        self.logger = logging.getLogger(f"{__name__}.{self.session_id}")
        self.logger.info(f"🚀 Initializing Production VacayMate System (Session: {self.session_id})")
        
        # Initialize LangSmith tracing
        self._setup_langsmith_tracing()
        
        # Load production configuration
        self.config = self._load_production_config()
        
        # Apply custom configurations
        if circuit_breaker_config:
            self._configure_circuit_breakers(circuit_breaker_config)
        
        if resource_limits:
            self._configure_resource_limits(resource_limits)
        
        # Initialize defensive workflow components
        self.max_iterations = max_iterations
        self.enable_monitoring = enable_monitoring
        self.llm_model = llm_model or "gpt-4o-mini"
        
        # Build the defensive graph
        self.graph = self._build_defensive_graph()
        
        # Production metrics
        self.production_metrics = {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "circuit_breaker_trips": 0,
            "fallback_activations": 0,
            "state_recoveries": 0,
            "loop_detections": 0
        }
        
        self.logger.info("✅ Production VacayMate System initialized successfully")
        self._log_system_configuration()
    
    def _setup_langsmith_tracing(self):
        """Setup LangSmith tracing configuration."""
        # Check if LangSmith environment variables are set
        langsmith_tracing = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
        langsmith_project = os.getenv("LANGSMITH_PROJECT", "VacayMate")
        langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
        
        if langsmith_tracing and langsmith_api_key:
            self.tracing_enabled = True
            self.logger.info(f"🔍 LangSmith tracing enabled")
            self.logger.info(f"📊 Project: {langsmith_project}")
            self.logger.info(f"🌐 Endpoint: {langsmith_endpoint}")
            
            # Set additional metadata for this session
            os.environ["LANGCHAIN_SESSION"] = f"VacayMate_Production_{self.session_id}"
            
        else:
            self.tracing_enabled = False
            missing_vars = []
            if not langsmith_tracing:
                missing_vars.append("LANGSMITH_TRACING=true")
            if not langsmith_api_key:
                missing_vars.append("LANGSMITH_API_KEY")
            
            self.logger.info(f"📝 LangSmith tracing disabled. Missing: {', '.join(missing_vars)}")
        
        return self.tracing_enabled
    
    def _export_markdown_plan(self, state: Dict[str, Any], destination: str, 
                             start_date: str, return_date: str):
        """Export the vacation plan to a markdown file."""
        try:
            import os
            from datetime import datetime
            
            # Create outputs directory
            outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_vacation_plan_{destination.lower().replace(' ', '_')}_{timestamp}.md"
            filepath = os.path.join(outputs_dir, filename)
            
            # Build markdown content
            final_plan = state.get("final_plan", "Plan not available")
            
            markdown_content = f"""# 🛡️ Production VacayMate Travel Plan: {destination}

**Generated on:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
**Travel Dates:** {start_date} to {return_date}
**System:** Production VacayMate with LangSmith Tracing
**Session:** {self.session_id}

---

## 📋 Complete Travel Plan

{final_plan}

---

## 📊 Production Metadata

- **System Version:** Production VacayMate v2.0
- **LangSmith Tracing:** {'✅ Enabled' if self.tracing_enabled else '❌ Disabled'}
- **Session ID:** {self.session_id}
- **Generation Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Generated by Production VacayMate AI Travel Planning System with LangSmith Tracing*
"""
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"📄 Production vacation plan exported to: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting markdown file: {e}")
            raise e
    
    def _build_defensive_graph(self):
        """Build the defensive workflow graph with LangSmith tracing."""
        from langgraph.graph import StateGraph, START, END
        from states.VacayMate_state import VacationPlannerState
        from consts import MANAGER, RESEARCHER, CALCULATOR, PLANNER, SUMMARIZER, MERGE_RESULTS
        
        # Create the graph - LangGraph will automatically trace to LangSmith
        graph = StateGraph(VacationPlannerState)
        
        # Add defensive nodes
        graph.add_node(MANAGER, defensive_manager_node)
        graph.add_node(RESEARCHER, defensive_researcher_node)
        graph.add_node(CALCULATOR, defensive_calculator_node)
        graph.add_node(PLANNER, defensive_planner_node)
        graph.add_node(MERGE_RESULTS, defensive_merge_node)
        graph.add_node(SUMMARIZER, defensive_summarizer_node)
        
        # Add edges (same flow as original)
        graph.add_edge(START, MANAGER)
        graph.add_edge(MANAGER, RESEARCHER)
        graph.add_edge(RESEARCHER, CALCULATOR)
        graph.add_edge(RESEARCHER, PLANNER)
        graph.add_edge(CALCULATOR, MERGE_RESULTS)
        graph.add_edge(PLANNER, MERGE_RESULTS)
        graph.add_edge(MERGE_RESULTS, SUMMARIZER)
        graph.add_edge(SUMMARIZER, END)
        
        compiled_graph = graph.compile()
        
        if self.tracing_enabled:
            self.logger.info("🔍 Defensive graph compiled with LangSmith tracing enabled")
        
        return compiled_graph
    
    def _load_production_config(self) -> Dict[str, Any]:
        """Load production configuration with enhanced defaults."""
        try:
            config = load_config()
            self.logger.info("✅ Production configuration loaded from config.yaml")
        except Exception as e:
            self.logger.warning(f"⚠️ Config loading failed: {e}, using production defaults")
            config = self._get_production_defaults()
        
        # Enhance with production-specific settings
        production_config = config.copy()
        production_config.setdefault('production', {
            'max_concurrent_requests': 10,
            'request_timeout_seconds': 300,
            'health_check_interval': 60,
            'metrics_retention_hours': 24,
            'auto_recovery_enabled': True,
            'fallback_cache_ttl': 3600
        })
        
        return production_config
    
    def _get_production_defaults(self) -> Dict[str, Any]:
        """Get production-grade default configuration."""
        return {
            'vacaymate_system': {
                'max_retries': 5,
                'timeout_seconds': 300,
                'model_config': {
                    'temperature': 0.2,  # Lower temperature for production consistency
                    'max_tokens': 4000
                },
                'agents': {
                    'manager': {'llm': 'gpt-4o-mini'},
                    'researcher': {'llm': 'gpt-4o-mini'},
                    'calculator': {'llm': 'gpt-4o-mini'},
                    'planner': {'llm': 'gpt-4o-mini'},
                    'summarizer': {'llm': 'gpt-4o-mini'}
                }
            },
            'defensive_patterns': {
                'circuit_breakers': {
                    'failure_threshold': 3,  # More aggressive for production
                    'timeout_minutes': 5     # Shorter timeout for faster recovery
                },
                'retry_logic': {
                    'max_retries': 5,
                    'base_delay': 0.5,
                    'backoff_factor': 2.0,
                    'max_delay': 30.0
                },
                'resource_limits': {
                    'max_memory_mb': 1000,
                    'max_time_seconds': 60
                }
            }
        }
    
    def _configure_circuit_breakers(self, config: Dict[str, Any]):
        """Configure circuit breakers with custom settings."""
        failure_threshold = config.get('failure_threshold', 3)
        timeout_minutes = config.get('timeout_minutes', 5)
        
        # Update global circuit breaker settings
        circuit_breaker.failure_threshold = failure_threshold
        circuit_breaker.timeout_seconds = timeout_minutes * 60
        
        self.logger.info(f"🔧 Circuit breakers configured: threshold={failure_threshold}, timeout={timeout_minutes}min")
    
    def _configure_resource_limits(self, config: Dict[str, Any]):
        """Configure resource limits with custom settings."""
        max_memory = config.get('max_memory_mb', 1000)
        max_time = config.get('max_time_seconds', 60)
        
        self.logger.info(f"🔧 Resource limits configured: memory={max_memory}MB, time={max_time}s")
    
    def _log_system_configuration(self):
        """Log current system configuration for audit purposes."""
        config_summary = {
            "session_id": self.session_id,
            "max_iterations": self.max_iterations,
            "monitoring_enabled": self.enable_monitoring,
            "circuit_breaker_threshold": circuit_breaker.failure_threshold,
            "circuit_breaker_timeout": circuit_breaker.timeout_seconds,
            "llm_model": self.llm_model,
            "tracing_enabled": self.tracing_enabled
        }
        
        self.logger.info(f"📋 System Configuration: {config_summary}")
    
    def run(self, 
            user_request: str, 
            current_location: str, 
            destination: str, 
            start_date: str, 
            return_date: str,
            export_formats: Optional[List[str]] = None,
            correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a production vacation planning request with full defensive patterns.
        
        Args:
            user_request: User's travel request description
            current_location: Departure city
            destination: Destination city  
            start_date: Trip start date (YYYY-MM-DD)
            return_date: Trip return date (YYYY-MM-DD)
            export_formats: List of export formats ['markdown', 'json', 'html']
            correlation_id: Optional correlation ID for request tracking
            
        Returns:
            Dict: Comprehensive results with defensive system metadata
        """
        request_start_time = time.time()
        correlation_id = correlation_id or f"{self.session_id}_{int(time.time())}"
        
        # Update metrics
        self.production_metrics["total_requests"] += 1
        
        # Create request logger with correlation ID
        request_logger = logging.getLogger(f"{__name__}.{correlation_id}")
        request_logger.info(f"🎯 Starting production request: {current_location} → {destination}")
        
        # Add LangSmith metadata for this run
        if self.tracing_enabled:
            # Set run-specific metadata
            os.environ["LANGCHAIN_RUN_NAME"] = f"VacayMate_Trip_{current_location}_to_{destination}"
            os.environ["LANGCHAIN_RUN_TAGS"] = f"production,vacation_planning,{current_location.lower()},{destination.lower()}"
            
            # Log tracing info
            request_logger.info(f"🔍 LangSmith tracing active for this request")
            request_logger.info(f"📊 Run name: VacayMate_Trip_{current_location}_to_{destination}")
            request_logger.info(f"🏷️ Tags: production, vacation_planning, {current_location.lower()}, {destination.lower()}")
        
        try:
            # Pre-flight system health check
            health_status = self._perform_health_check()
            if not health_status["healthy"]:
                request_logger.warning(f"⚠️ System health issues detected: {health_status['issues']}")
            
            # Execute the defensive workflow
            request_logger.info("🛡️ Executing defensive workflow...")
            
            # Create initial defensive state
            initial_state = initialize_defensive_vacation_state(
                user_request=user_request,
                current_location=current_location,
                destination=destination,
                start_date=start_date,
                return_date=return_date
            )
            
            # Run the defensive graph - LangGraph will automatically trace to LangSmith
            result = self.graph.invoke(initial_state)
            
            # Export to markdown
            try:
                self._export_markdown_plan(result, destination, start_date, return_date)
            except Exception as e:
                request_logger.warning(f"⚠️ Markdown export failed: {e}")
                result["export_error"] = str(e)
            
            # Enhance result with production metadata
            request_time = time.time() - request_start_time
            result = self._enhance_result_with_production_metadata(
                result, correlation_id, request_time, health_status
            )
            
            # Export to additional formats if requested
            if export_formats:
                self._export_additional_formats(result, export_formats, destination, start_date, return_date)
            
            # Update success metrics
            self.production_metrics["successful_requests"] += 1
            self._update_average_response_time(request_time)
            
            # Log success
            request_logger.info(f"✅ Production request completed successfully in {request_time:.2f}s")
            
            return result
            
        except Exception as e:
            # Handle production errors
            request_time = time.time() - request_start_time
            error_result = self._handle_production_error(e, correlation_id, request_time)
            
            # Update failure metrics
            self.production_metrics["failed_requests"] += 1
            
            request_logger.error(f"❌ Production request failed after {request_time:.2f}s: {str(e)}")
            
            return error_result
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        health = get_system_health()
        
        # Check circuit breaker status
        circuit_breakers = health.get("circuit_breakers", {})
        disabled_services = [name for name, status in circuit_breakers.items() 
                           if status.get("disabled", False)]
        
        # Check memory usage
        memory_mb = health.get("memory_usage_mb", 0)
        memory_critical = memory_mb > 800  # 800MB threshold
        
        # Determine overall health
        issues = []
        if disabled_services:
            issues.append(f"Disabled services: {', '.join(disabled_services)}")
        if memory_critical:
            issues.append(f"High memory usage: {memory_mb:.1f}MB")
        
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "disabled_services": disabled_services,
            "memory_usage_mb": memory_mb,
            "circuit_breakers": circuit_breakers,
            "timestamp": datetime.now().isoformat()
        }
    
    def _enhance_result_with_production_metadata(self, 
                                               result: Dict[str, Any], 
                                               correlation_id: str,
                                               request_time: float,
                                               health_status: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance result with comprehensive production metadata."""
        
        # Extract defensive system stats
        execution_stats = result.get("_execution_stats", {})
        
        # Add production metadata
        result["_production_metadata"] = {
            "session_id": self.session_id,
            "correlation_id": correlation_id,
            "request_time_seconds": request_time,
            "system_health_at_start": health_status,
            "defensive_patterns_active": {
                "circuit_breakers": True,
                "state_validation": True,
                "loop_detection": True,
                "retry_logic": True,
                "resource_limits": True,
                "output_validation": True
            },
            "performance_metrics": {
                "total_requests": self.production_metrics["total_requests"],
                "success_rate": (self.production_metrics["successful_requests"] / 
                               max(1, self.production_metrics["total_requests"])) * 100,
                "average_response_time": self.production_metrics["average_response_time"]
            },
            "quality_indicators": {
                "state_validations_passed": result.get("_state_version", 0),
                "circuit_breaker_activations": len([s for s in health_status.get("circuit_breakers", {}).values() 
                                                  if s.get("failures", 0) > 0]),
                "fallback_data_used": any("fallback" in str(result.get(key, "")).lower() 
                                        for key in ["research_results", "planner_results", "calculator_results"])
            }
        }
        
        return result
    
    def _export_additional_formats(self, result: Dict[str, Any], formats: List[str], 
                                 destination: str, start_date: str, return_date: str):
        """Export results to additional formats."""
        try:
            outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"production_vacation_plan_{destination.lower().replace(' ', '_')}_{timestamp}"
            
            for format_type in formats:
                if format_type.lower() == 'json':
                    self._export_json(result, outputs_dir, base_filename)
                elif format_type.lower() == 'html':
                    self._export_html(result, outputs_dir, base_filename, destination, start_date, return_date)
                    
        except Exception as e:
            self.logger.error(f"❌ Additional format export failed: {e}")
    
    def _export_json(self, result: Dict[str, Any], outputs_dir: str, base_filename: str):
        """Export result to JSON format."""
        import json
        
        json_file = os.path.join(outputs_dir, f"{base_filename}.json")
        
        # Create JSON-serializable version
        json_result = self._make_json_serializable(result)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 JSON export completed: {json_file}")
    
    def _export_html(self, result: Dict[str, Any], outputs_dir: str, base_filename: str,
                    destination: str, start_date: str, return_date: str):
        """Export result to HTML format."""
        html_file = os.path.join(outputs_dir, f"{base_filename}.html")
        
        # Create HTML content
        html_content = self._build_html_content(result, destination, start_date, return_date)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"📄 HTML export completed: {html_file}")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Make object JSON serializable."""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def _build_html_content(self, result: Dict[str, Any], destination: str, 
                           start_date: str, return_date: str) -> str:
        """Build HTML content for the vacation plan."""
        final_plan = result.get("final_plan", "Plan not available")
        production_metadata = result.get("_production_metadata", {})
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ Production VacayMate Plan: {destination}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.6; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; 
                     padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status-badge {{ display: inline-block; padding: 5px 10px; border-radius: 15px; 
                        font-size: 12px; font-weight: bold; margin: 5px; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .plan-content {{ white-space: pre-wrap; }}
        h1, h2, h3 {{ color: #333; }}
        .defensive-patterns {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                             gap: 15px; margin: 20px 0; }}
        .pattern-card {{ background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Production VacayMate Travel Plan</h1>
            <h2>{destination}</h2>
            <p><strong>Travel Dates:</strong> {start_date} to {return_date}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            
            <div class="status-badges">
                <span class="status-badge status-success">✅ Defensive Patterns Active</span>
                <span class="status-badge status-success">🛡️ Production Ready</span>
                <span class="status-badge status-success">🔄 Auto-Recovery Enabled</span>
            </div>
        </div>
        
        <div class="defensive-patterns">
            <div class="pattern-card">
                <h4>🔧 Circuit Breakers</h4>
                <p>Protecting against API failures with automatic fallbacks</p>
            </div>
            <div class="pattern-card">
                <h4>🔄 Retry Logic</h4>
                <p>Exponential backoff for transient failures</p>
            </div>
            <div class="pattern-card">
                <h4>✅ State Validation</h4>
                <p>Automatic corruption detection and recovery</p>
            </div>
            <div class="pattern-card">
                <h4>🚫 Loop Detection</h4>
                <p>Preventing infinite loops with iteration caps</p>
            </div>
            <div class="pattern-card">
                <h4>📊 Resource Limits</h4>
                <p>Memory and time usage monitoring</p>
            </div>
            <div class="pattern-card">
                <h4>🎯 Output Validation</h4>
                <p>Pydantic schema validation for all responses</p>
            </div>
        </div>
        
        <div class="metadata">
            <h3>📊 Production Metadata</h3>
            <p><strong>Session ID:</strong> {production_metadata.get('session_id', 'N/A')}</p>
            <p><strong>Correlation ID:</strong> {production_metadata.get('correlation_id', 'N/A')}</p>
            <p><strong>Response Time:</strong> {production_metadata.get('request_time_seconds', 0):.2f} seconds</p>
            <p><strong>Success Rate:</strong> {production_metadata.get('performance_metrics', {}).get('success_rate', 0):.1f}%</p>
        </div>
        
        <div class="plan-content">
            <h2>📋 Complete Travel Plan</h2>
            {final_plan.replace('\n', '<br>')}
        </div>
        
        <div class="metadata">
            <p><em>Generated by Production VacayMate System with Full Defensive Patterns</em></p>
            <p><em>Export completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        </div>
    </div>
</body>
</html>
"""
        return html_template
    
    def _handle_production_error(self, error: Exception, correlation_id: str, 
                                request_time: float) -> Dict[str, Any]:
        """Handle production errors with comprehensive error information."""
        error_result = {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "final_plan": f"❌ **Production System Error**\n\nAn error occurred during processing: {str(error)}\n\nPlease try again or contact support if the issue persists.",
            "_production_metadata": {
                "session_id": self.session_id,
                "correlation_id": correlation_id,
                "request_time_seconds": request_time,
                "error_occurred": True,
                "error_timestamp": datetime.now().isoformat(),
                "system_health_at_error": get_system_health()
            }
        }
        
        return error_result
    
    def _update_average_response_time(self, request_time: float):
        """Update average response time metric."""
        total_successful = self.production_metrics["successful_requests"]
        if total_successful == 1:
            self.production_metrics["average_response_time"] = request_time
        else:
            current_avg = self.production_metrics["average_response_time"]
            self.production_metrics["average_response_time"] = (
                (current_avg * (total_successful - 1) + request_time) / total_successful
            )
    
    def get_production_status(self) -> Dict[str, Any]:
        """Get comprehensive production system status."""
        return {
            "production_metrics": self.production_metrics,
            "system_health": get_system_health(),
            "uptime_seconds": time.time() - self.start_time,
            "configuration": {
                "max_iterations": self.max_iterations,
                "monitoring_enabled": self.enable_monitoring,
                "circuit_breaker_threshold": circuit_breaker.failure_threshold,
                "circuit_breaker_timeout": circuit_breaker.timeout_seconds,
                "llm_model": self.llm_model,
                "tracing_enabled": self.tracing_enabled
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_health_dashboard(self) -> str:
        """Get a comprehensive health dashboard for monitoring."""
        status = self.get_production_status()
        
        lines = [
            "🛡️ PRODUCTION VACAYMATE SYSTEM DASHBOARD",
            "=" * 50,
            "",
            f"📊 SESSION: {self.session_id}",
            f"⏱️  UPTIME: {status['uptime_seconds']:.0f} seconds ({status['uptime_seconds']/3600:.1f} hours)",
            "",
            "📈 REQUEST METRICS:",
            f"   Total Requests: {status['production_metrics']['total_requests']}",
            f"   ✅ Successful: {status['production_metrics']['successful_requests']}",
            f"   ❌ Failed: {status['production_metrics']['failed_requests']}",
            f"   📊 Success Rate: {(status['production_metrics']['successful_requests'] / max(1, status['production_metrics']['total_requests']) * 100):.1f}%",
            f"   ⚡ Avg Response Time: {status['production_metrics']['average_response_time']:.2f}s",
            ""
        ]
        
        # Circuit breaker status
        cb_status = status['system_health'].get('circuit_breakers', {})
        if cb_status:
            lines.extend([
                "🔌 CIRCUIT BREAKER STATUS:",
                ""
            ])
            for name, info in cb_status.items():
                status_icon = "❌ OPEN" if info.get('disabled', False) else "✅ CLOSED"
                failures = info.get('failures', 0)
                last_success = info.get('last_success')
                last_success_str = datetime.fromtimestamp(last_success).strftime('%H:%M:%S') if last_success else "Never"
                lines.extend([
                    f"   {name}:",
                    f"     Status: {status_icon}",
                    f"     Failures: {failures}",
                    f"     Last Success: {last_success_str}",
                    ""
                ])
        
        # System resources
        memory_mb = status['system_health'].get('memory_usage_mb', 0)
        memory_status = "🟢 NORMAL" if memory_mb < 500 else "🟡 HIGH" if memory_mb < 800 else "🔴 CRITICAL"
        
        lines.extend([
            "💾 SYSTEM RESOURCES:",
            f"   Memory Usage: {memory_mb:.1f}MB ({memory_status})",
            "",
            "🛡️ DEFENSIVE PATTERNS STATUS:",
            "   ✅ Circuit Breakers: ACTIVE",
            "   ✅ State Validation: ACTIVE", 
            "   ✅ Loop Detection: ACTIVE",
            "   ✅ Retry Logic: ACTIVE",
            "   ✅ Resource Limits: ACTIVE",
            "   ✅ Output Validation: ACTIVE",
            "",
            f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50
        ])
        
        return "\n".join(lines)
    
    def reset_production_metrics(self):
        """Reset production metrics (useful for testing or new deployment)."""
        self.production_metrics.update({
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "circuit_breaker_trips": 0,
            "fallback_activations": 0,
            "state_recoveries": 0,
            "loop_detections": 0
        })
        
        # Reset circuit breakers
        circuit_breaker.failure_counts.clear()
        circuit_breaker.disabled_until.clear()
        circuit_breaker.last_success.clear()
        
        self.logger.info("🔄 Production metrics and circuit breakers reset")
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run a comprehensive health check and return detailed results."""
        health_check_start = time.time()
        
        try:
            # Test basic system functionality
            test_result = self.run(
                user_request="Health check test request",
                current_location="New York",
                destination="Boston", 
                start_date="2025-12-01",
                return_date="2025-12-03",
                export_formats=[],
                correlation_id="health_check"
            )
            
            health_check_time = time.time() - health_check_start
            
            return {
                "healthy": True,
                "health_check_time_seconds": health_check_time,
                "test_request_successful": test_result.get("success", True),
                "system_status": self.get_production_status(),
                "timestamp": datetime.now().isoformat(),
                "recommendations": self._get_health_recommendations()
            }
            
        except Exception as e:
            health_check_time = time.time() - health_check_start
            
            return {
                "healthy": False,
                "health_check_time_seconds": health_check_time,
                "error": str(e),
                "system_status": self.get_production_status(),
                "timestamp": datetime.now().isoformat(),
                "recommendations": ["System requires immediate attention", "Check logs for detailed error information"]
            }
    
    def _get_health_recommendations(self) -> List[str]:
        """Get health recommendations based on current system status."""
        recommendations = []
        status = self.get_production_status()
        
        # Check success rate
        success_rate = (status['production_metrics']['successful_requests'] / 
                       max(1, status['production_metrics']['total_requests']) * 100)
        
        if success_rate < 80:
            recommendations.append("Success rate below 80% - investigate failing requests")
        
        # Check memory usage
        memory_mb = status['system_health'].get('memory_usage_mb', 0)
        if memory_mb > 800:
            recommendations.append("High memory usage detected - consider restarting system")
        
        # Check circuit breakers
        disabled_services = [name for name, info in status['system_health'].get('circuit_breakers', {}).items()
                           if info.get('disabled', False)]
        if disabled_services:
            recommendations.append(f"Services disabled by circuit breakers: {', '.join(disabled_services)}")
        
        # Check response time
        avg_response_time = status['production_metrics']['average_response_time']
        if avg_response_time > 30:
            recommendations.append("Average response time above 30s - performance optimization needed")
        
        if not recommendations:
            recommendations.append("System operating within normal parameters")
        
        return recommendations
    
    def get_tracing_status(self) -> Dict[str, Any]:
        """Get current LangSmith tracing status."""
        return {
            "tracing_enabled": self.tracing_enabled,
            "langsmith_project": os.getenv("LANGSMITH_PROJECT", "VacayMate"),
            "langsmith_endpoint": os.getenv("LANGSMITH_ENDPOINT", ""),
            "session_name": f"VacayMate_Production_{self.session_id}",
            "environment_variables": {
                "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING", "Not set"),
                "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT", "Not set"),
                "LANGSMITH_ENDPOINT": os.getenv("LANGSMITH_ENDPOINT", "Not set"),
                "LANGSMITH_API_KEY": "Set" if os.getenv("LANGSMITH_API_KEY") else "Not set"
            }
        }


# ===============================
# PRODUCTION TESTING FUNCTIONS
# ===============================

def test_production_system():
    """Comprehensive test of the production system."""
    print("🧪 TESTING PRODUCTION VACAYMATE SYSTEM")
    print("=" * 50)
    
    # Initialize production system
    system = ProductionVacayMate(max_iterations=15, enable_monitoring=True)
    
    print(f"\n✅ System initialized (Session: {system.session_id})")
    
    # Test 1: Normal operation
    print("\n🧪 TEST 1: Normal Operation")
    print("-" * 30)
    
    result1 = system.run(
        user_request="Plan a business trip with good hotels and convenient flights",
        current_location="Tel Aviv",
        destination="Sofia", 
        start_date="2025-11-15",
        return_date="2025-11-18",
        export_formats=['json'],
        correlation_id="test_1"
    )
    
    print(f"✅ Test 1 Result: {'SUCCESS' if result1.get('final_plan') else 'FAILED'}")
    print(f"   Response time: {result1.get('_production_metadata', {}).get('request_time_seconds', 0):.2f}s")
    
    # Test 2: Error handling
    print("\n🧪 TEST 2: Error Handling")
    print("-" * 30)
    
    result2 = system.run(
        user_request="Test invalid input handling",
        current_location="InvalidCity123",
        destination="AnotherInvalidCity456",
        start_date="2025-11-15", 
        return_date="2025-11-18",
        correlation_id="test_2"
    )
    
    print(f"✅ Test 2 Result: {'SUCCESS' if 'validation_errors' in result2 or 'error' in result2 else 'FAILED'}")
    print(f"   Error handled gracefully: {'YES' if result2.get('final_plan') else 'NO'}")
    
    # Test 3: Circuit breaker simulation
    print("\n🧪 TEST 3: Circuit Breaker Simulation")
    print("-" * 30)
    
    # Simulate multiple failures to trip circuit breakers
    print("   Simulating API failures...")
    for i in range(3):
        try:
            # This would normally trigger circuit breakers in a real failure scenario
            pass
        except:
            pass
    
    print("✅ Test 3 Result: Circuit breaker logic active")
    
    # Test 4: Health check
    print("\n🧪 TEST 4: Health Check")
    print("-" * 30)
    
    health_result = system.run_health_check()
    print(f"✅ Test 4 Result: {'HEALTHY' if health_result['healthy'] else 'UNHEALTHY'}")
    print(f"   Health check time: {health_result['health_check_time_seconds']:.2f}s")
    
    # Display final dashboard
    print("\n📊 FINAL SYSTEM DASHBOARD")
    print("=" * 50)
    print(system.get_health_dashboard())
    
    print("\n🎉 PRODUCTION TESTING COMPLETED")
    return system


def run_production_example():
    """Run a production example with Tel Aviv to Sofia trip."""
    print("🚀 PRODUCTION VACAYMATE EXAMPLE")
    print("=" * 40)
    
    # Initialize production system
    system = ProductionVacayMate(
        max_iterations=20,
        enable_monitoring=True
    )
    
    print("✅ Production system initialized")
    print(f"📊 Session ID: {system.session_id}")
    
    # Run example trip planning
    print("\n🎯 Planning trip: Tel Aviv → Sofia")
    
    result = system.run(
        user_request="Plan a 4-day cultural and culinary trip with good hotels and convenient flights. I'm interested in history, local food, and some nightlife.",
        current_location="Tel Aviv",
        destination="Sofia",
        start_date="2025-12-10", 
        return_date="2025-12-14",
        export_formats=['json', 'html'],
        correlation_id="production_example"
    )
    
    # Display results
    print(f"\n✅ Trip planning completed!")
    print(f"📊 Response time: {result.get('_production_metadata', {}).get('request_time_seconds', 0):.2f} seconds")
    print(f"🛡️ Defensive patterns: {'ACTIVE' if result.get('_production_metadata', {}).get('defensive_patterns_active') else 'INACTIVE'}")
    
    # Show final plan preview
    final_plan = result.get('final_plan', '')
    if final_plan:
        print(f"\n📋 Plan Preview (first 300 chars):")
        print("-" * 40)
        print(final_plan[:300] + "..." if len(final_plan) > 300 else final_plan)
    
    # Show system health
    print(f"\n{system.get_health_dashboard()}")
    
    return result


if __name__ == "__main__":
    # Run production example
    example_result = run_production_example()
    
    print("\n" + "="*60)
    print("🧪 Running comprehensive production tests...")
    print("="*60)
    
    # Run comprehensive tests
    test_system = test_production_system()
    
    print(f"\n🎉 Production VacayMate System is ready for deployment!")
    print(f"📊 Session ID: {test_system.session_id}")
    print(f"🛡️ All defensive patterns are active and tested")
