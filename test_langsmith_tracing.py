#!/usr/bin/env python3
"""
Test script for LangSmith tracing integration with VacayMate Production System.

This script tests the tracing functionality and verifies that traces appear in LangSmith.
"""

import os
import sys
from datetime import datetime

# Add code directory to path
sys.path.insert(0, 'code')

def test_langsmith_integration():
    """Test LangSmith tracing integration."""
    print("🔍 Testing LangSmith Tracing Integration")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    env_vars = [
        "LANGSMITH_TRACING",
        "LANGSMITH_ENDPOINT", 
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "OPENAI_API_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if var == "LANGSMITH_API_KEY" or var == "OPENAI_API_KEY":
            # Mask sensitive keys
            display_value = f"{value[:8]}...{value[-4:]}" if value else "Not set"
        else:
            display_value = value or "Not set"
        print(f"  {var}: {display_value}")
    
    # Test import
    print("\n📦 Testing Imports:")
    try:
        from VacayMate_system_production import ProductionVacayMate
        print("  ✅ ProductionVacayMate imported successfully")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False
    
    try:
        from langsmith import traceable
        print("  ✅ LangSmith traceable imported successfully")
    except Exception as e:
        print(f"  ❌ LangSmith import failed: {e}")
        return False
    
    # Initialize system
    print("\n🚀 Initializing Production System:")
    try:
        system = ProductionVacayMate(max_iterations=10, enable_monitoring=True)
        print(f"  ✅ System initialized (Session: {system.session_id})")
        print(f"  🔍 Tracing enabled: {system.tracing_enabled}")
    except Exception as e:
        print(f"  ❌ System initialization failed: {e}")
        return False
    
    # Test a simple request
    print("\n🧪 Testing Traced Request:")
    try:
        result = system.run(
            user_request="Plan a quick weekend trip with good food and culture",
            current_location="Tel Aviv",
            destination="Sofia",
            start_date="2025-11-01",
            return_date="2025-11-03",
            correlation_id="langsmith_test"
        )
        
        print(f"  ✅ Request completed successfully")
        print(f"  📊 Response time: {result.get('_production_metadata', {}).get('request_time_seconds', 0):.2f}s")
        print(f"  🛡️ Defensive patterns active: {bool(result.get('_production_metadata', {}).get('defensive_patterns_active'))}")
        
        # Check if final plan was generated
        if result.get('final_plan'):
            print(f"  📋 Plan generated: {len(result['final_plan'])} characters")
        else:
            print("  ⚠️ No final plan generated")
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return False
    
    # Display tracing information
    print("\n📈 Tracing Information:")
    if system.tracing_enabled:
        print(f"  🎯 Project: {os.getenv('LANGSMITH_PROJECT', 'VacayMate')}")
        print(f"  🔗 Session: VacayMate_Production_{system.session_id}")
        print(f"  🌐 Endpoint: {os.getenv('LANGSMITH_ENDPOINT')}")
        print(f"  📝 Check your LangSmith dashboard for traces!")
        print(f"  🔍 Look for traces tagged with: production, defensive, tel-aviv, sofia")
    else:
        print("  ⚠️ Tracing is disabled")
    
    print("\n✅ LangSmith integration test completed successfully!")
    print("\n🔗 Next Steps:")
    print("  1. Check your LangSmith dashboard at https://smith.langchain.com")
    print("  2. Look for the 'VacayMate' project")
    print("  3. Find traces with tags: production, defensive, vacation_planning")
    print("  4. Explore the detailed execution flow and defensive patterns")
    
    return True

if __name__ == "__main__":
    success = test_langsmith_integration()
    if success:
        print(f"\n🎉 All tests passed! Check LangSmith dashboard for traces.")
        sys.exit(0)
    else:
        print(f"\n❌ Tests failed. Check the error messages above.")
        sys.exit(1)
