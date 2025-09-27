#!/usr/bin/env python3
"""
Test LangSmith integration with VacayMate Production System.
This script loads environment variables and tests the tracing functionality.
"""

import os
import sys

def load_env_file():
    """Load environment variables from .env file."""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📁 Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value
        print("✅ Environment variables loaded")
    else:
        print(f"⚠️ No .env file found at {env_file}")

def test_langsmith_tracing():
    """Test LangSmith tracing with VacayMate."""
    print("\n🔍 Testing LangSmith Integration with VacayMate")
    print("=" * 60)
    
    # Load environment variables
    load_env_file()
    
    # Add code directory to path
    sys.path.insert(0, 'code')
    
    # Import and initialize system
    try:
        from VacayMate_system_production import ProductionVacayMate
        print("✅ ProductionVacayMate imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Initialize system
    try:
        system = ProductionVacayMate(max_iterations=10, enable_monitoring=True)
        print(f"✅ System initialized (Session: {system.session_id})")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False
    
    # Check tracing status
    tracing_status = system.get_tracing_status()
    print(f"\n📊 Tracing Status:")
    print(f"  🔍 Enabled: {tracing_status['tracing_enabled']}")
    print(f"  📊 Project: {tracing_status['langsmith_project']}")
    print(f"  🌐 Endpoint: {tracing_status['langsmith_endpoint']}")
    print(f"  📝 Session: {tracing_status['session_name']}")
    
    if not tracing_status['tracing_enabled']:
        print("\n⚠️ LangSmith tracing is disabled. Check your environment variables:")
        for var, value in tracing_status['environment_variables'].items():
            status = "✅" if value != "Not set" else "❌"
            print(f"    {status} {var}: {value}")
        return False
    
    print(f"\n🎯 Running test vacation planning request...")
    print(f"📍 Route: Tel Aviv → Sofia")
    print(f"📅 Dates: 2025-12-01 to 2025-12-05")
    
    # Run a test request
    try:
        result = system.run(
            user_request="Plan a 4-day cultural trip with great food and historical sites",
            current_location="Tel Aviv",
            destination="Sofia",
            start_date="2025-12-01",
            return_date="2025-12-05",
            correlation_id="langsmith_integration_test"
        )
        
        print(f"\n✅ Test request completed successfully!")
        
        # Display results
        metadata = result.get('_production_metadata', {})
        print(f"📊 Response time: {metadata.get('request_time_seconds', 0):.2f} seconds")
        print(f"🛡️ Defensive patterns active: {bool(metadata.get('defensive_patterns_active'))}")
        
        # Check results
        research_results = result.get('research_results', {})
        flights = research_results.get('flights', [])
        hotels = research_results.get('accommodations', {}).get('hotels', [])
        
        print(f"\n📋 Results Summary:")
        print(f"  ✈️ Flights found: {len(flights)}")
        print(f"  🏨 Hotels found: {len(hotels)}")
        print(f"  📝 Final plan: {'✅ Generated' if result.get('final_plan') else '❌ Missing'}")
        
        print(f"\n🎉 LangSmith integration test completed successfully!")
        print(f"\n🔗 Check your LangSmith dashboard:")
        print(f"  🌐 URL: https://smith.langchain.com")
        print(f"  📊 Project: {tracing_status['langsmith_project']}")
        print(f"  📝 Session: {tracing_status['session_name']}")
        print(f"  🏷️ Look for run: VacayMate_Trip_Tel_Aviv_to_Sofia")
        print(f"  🔍 Tags: production, vacation_planning, tel-aviv, sofia")
        
        return True
        
    except Exception as e:
        print(f"❌ Test request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_langsmith_tracing()
    if success:
        print(f"\n🎊 All tests passed! Your VacayMate system is now traced with LangSmith!")
    else:
        print(f"\n💥 Tests failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
