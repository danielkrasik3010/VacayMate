#!/usr/bin/env python3
"""
Full test of LangSmith tracing with a complete vacation planning request.
"""

import os
import sys

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env_file()
sys.path.insert(0, 'code')

def test_full_vacation_planning():
    """Test full vacation planning with LangSmith tracing."""
    print("🔍 Full VacayMate LangSmith Tracing Test")
    print("=" * 50)
    
    from VacayMate_system_production import ProductionVacayMate
    
    # Initialize system
    system = ProductionVacayMate(max_iterations=15, enable_monitoring=True)
    print(f"✅ System initialized (Session: {system.session_id})")
    print(f"🔍 Tracing enabled: {system.tracing_enabled}")
    
    if not system.tracing_enabled:
        print("⚠️ Tracing is disabled - check your environment variables")
        return False
    
    print(f"\n🎯 Planning vacation: Tel Aviv → Sofia")
    print(f"📅 Dates: 2025-11-15 to 2025-11-18")
    print(f"🔗 LangSmith Project: {os.getenv('LANGSMITH_PROJECT', 'VacayMate')}")
    print(f"🌐 Dashboard: https://smith.langchain.com")
    
    # Run full vacation planning
    try:
        result = system.run(
            user_request="Plan a 4-day cultural trip with great food, historical sites, and some nightlife. I want good hotels and convenient flights.",
            current_location="Tel Aviv",
            destination="Sofia",
            start_date="2025-11-15",
            return_date="2025-11-18",
            correlation_id="full_tracing_test"
        )
        
        print(f"\n✅ Vacation planning completed!")
        
        # Display results summary
        metadata = result.get('_production_metadata', {})
        print(f"📊 Response time: {metadata.get('request_time_seconds', 0):.2f} seconds")
        print(f"🛡️ Defensive patterns active: {bool(metadata.get('defensive_patterns_active'))}")
        print(f"🔗 Correlation ID: {metadata.get('correlation_id', 'N/A')}")
        
        # Check if we have results
        research_results = result.get('research_results', {})
        flights = research_results.get('flights', [])
        hotels = research_results.get('accommodations', {}).get('hotels', [])
        
        print(f"\n📋 Results Summary:")
        print(f"  ✈️ Flights found: {len(flights)}")
        print(f"  🏨 Hotels found: {len(hotels)}")
        print(f"  📝 Final plan: {'✅ Generated' if result.get('final_plan') else '❌ Missing'}")
        
        # Show plan preview
        final_plan = result.get('final_plan', '')
        if final_plan:
            print(f"\n📖 Plan Preview (first 200 chars):")
            print("-" * 40)
            print(final_plan[:200] + "..." if len(final_plan) > 200 else final_plan)
        
        print(f"\n🎉 Full test completed successfully!")
        print(f"🔍 Check your LangSmith dashboard for detailed traces:")
        print(f"   - Project: {os.getenv('LANGSMITH_PROJECT', 'VacayMate')}")
        print(f"   - Session: VacayMate_Production_{system.session_id}")
        print(f"   - Tags: production, defensive, tel-aviv, sofia")
        print(f"   - Correlation ID: full_tracing_test")
        
        return True
        
    except Exception as e:
        print(f"❌ Vacation planning failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_vacation_planning()
    sys.exit(0 if success else 1)
