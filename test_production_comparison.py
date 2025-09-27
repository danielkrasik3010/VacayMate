"""
Test script to compare VacayMate_system.py vs VacayMate_system_production.py
with valid input: Tel Aviv to Sofia, 2025-10-10 to 2025-10-17
"""

import sys
import os
import time
from datetime import datetime

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

def test_original_system():
    """Test the original VacayMate system."""
    print("🔵 TESTING ORIGINAL VACAYMATE SYSTEM")
    print("=" * 50)
    
    try:
        from VacayMate_system import VacayMate
        
        # Initialize original system
        original_system = VacayMate(llm_model="gpt-4o-mini")
        
        print("✅ Original system initialized")
        
        # Test with valid input
        start_time = time.time()
        
        result = original_system.run(
            user_request="Plan a cultural and culinary trip with good hotels and convenient flights. I'm interested in history, local food, and some sightseeing.",
            current_location="Tel Aviv",
            destination="Sofia",
            start_date="2025-10-10",
            return_date="2025-10-17"
        )
        
        end_time = time.time()
        
        print(f"✅ Original system completed in {end_time - start_time:.2f} seconds")
        
        # Analyze results
        final_plan = result.get("final_plan", "")
        research_results = result.get("research_results", {})
        calculator_results = result.get("calculator_results", {})
        planner_results = result.get("planner_results", {})
        
        print(f"📊 Results Analysis:")
        print(f"   Final plan length: {len(final_plan)} characters")
        print(f"   Flights found: {len(research_results.get('flights', []))}")
        print(f"   Hotels found: {len(research_results.get('accommodations', {}).get('hotels', []))}")
        print(f"   Weather forecast: {'✅' if planner_results.get('weather_forecast') else '❌'}")
        print(f"   Local events: {len(planner_results.get('local_events', []))}")
        print(f"   Cost calculation: {'✅' if calculator_results.get('final_quotation') else '❌'}")
        
        return {
            "success": True,
            "runtime": end_time - start_time,
            "final_plan_length": len(final_plan),
            "flights_count": len(research_results.get('flights', [])),
            "hotels_count": len(research_results.get('accommodations', {}).get('hotels', [])),
            "has_weather": bool(planner_results.get('weather_forecast')),
            "events_count": len(planner_results.get('local_events', [])),
            "has_cost": bool(calculator_results.get('final_quotation')),
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Original system failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "runtime": 0
        }

def test_production_system():
    """Test the production VacayMate system."""
    print("\n🛡️ TESTING PRODUCTION VACAYMATE SYSTEM")
    print("=" * 50)
    
    try:
        from VacayMate_system_production import ProductionVacayMate
        
        # Initialize production system
        production_system = ProductionVacayMate(
            max_iterations=20,
            enable_monitoring=True
        )
        
        print("✅ Production system initialized")
        print(f"📊 Session ID: {production_system.session_id}")
        
        # Test with valid input
        start_time = time.time()
        
        result = production_system.run(
            user_request="Plan a cultural and culinary trip with good hotels and convenient flights. I'm interested in history, local food, and some sightseeing.",
            current_location="Tel Aviv",
            destination="Sofia",
            start_date="2025-10-10",
            return_date="2025-10-17",
            export_formats=['json'],
            correlation_id="comparison_test"
        )
        
        end_time = time.time()
        
        print(f"✅ Production system completed in {end_time - start_time:.2f} seconds")
        
        # Analyze results
        final_plan = result.get("final_plan", "")
        research_results = result.get("research_results", {})
        calculator_results = result.get("calculator_results", {})
        planner_results = result.get("planner_results", {})
        production_metadata = result.get("_production_metadata", {})
        
        print(f"📊 Results Analysis:")
        print(f"   Final plan length: {len(final_plan)} characters")
        print(f"   Flights found: {len(research_results.get('flights', []))}")
        print(f"   Hotels found: {len(research_results.get('accommodations', {}).get('hotels', []))}")
        print(f"   Weather forecast: {'✅' if planner_results.get('weather_forecast') else '❌'}")
        print(f"   Local events: {len(planner_results.get('local_events', []))}")
        print(f"   Cost calculation: {'✅' if calculator_results.get('final_quotation') else '❌'}")
        
        print(f"🛡️ Defensive Patterns Status:")
        defensive_patterns = production_metadata.get("defensive_patterns_active", {})
        for pattern, active in defensive_patterns.items():
            status = "✅" if active else "❌"
            print(f"   {status} {pattern.replace('_', ' ').title()}")
        
        # Show system health
        print(f"\n{production_system.get_health_dashboard()}")
        
        return {
            "success": True,
            "runtime": end_time - start_time,
            "final_plan_length": len(final_plan),
            "flights_count": len(research_results.get('flights', [])),
            "hotels_count": len(research_results.get('accommodations', {}).get('hotels', [])),
            "has_weather": bool(planner_results.get('weather_forecast')),
            "events_count": len(planner_results.get('local_events', [])),
            "has_cost": bool(calculator_results.get('final_quotation')),
            "defensive_patterns_active": len([p for p in defensive_patterns.values() if p]),
            "system_health": production_system.get_production_status(),
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Production system failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "runtime": 0
        }

def compare_results(original_result, production_result):
    """Compare results from both systems."""
    print("\n📊 COMPARISON ANALYSIS")
    print("=" * 50)
    
    if not original_result["success"] or not production_result["success"]:
        print("❌ Cannot compare - one or both systems failed")
        if not original_result["success"]:
            print(f"   Original system error: {original_result.get('error', 'Unknown')}")
        if not production_result["success"]:
            print(f"   Production system error: {production_result.get('error', 'Unknown')}")
        return
    
    # Performance comparison
    print("⚡ PERFORMANCE COMPARISON:")
    print(f"   Original Runtime:   {original_result['runtime']:.2f}s")
    print(f"   Production Runtime: {production_result['runtime']:.2f}s")
    
    overhead = ((production_result['runtime'] - original_result['runtime']) / original_result['runtime']) * 100
    print(f"   Overhead:          {overhead:+.1f}%")
    
    # Functionality comparison
    print("\n🔧 FUNCTIONALITY COMPARISON:")
    
    metrics = [
        ("Final Plan Length", "final_plan_length"),
        ("Flights Found", "flights_count"),
        ("Hotels Found", "hotels_count"),
        ("Events Found", "events_count"),
        ("Has Weather", "has_weather"),
        ("Has Cost Calc", "has_cost")
    ]
    
    for metric_name, metric_key in metrics:
        orig_val = original_result.get(metric_key, 0)
        prod_val = production_result.get(metric_key, 0)
        
        if isinstance(orig_val, bool) and isinstance(prod_val, bool):
            status = "✅ SAME" if orig_val == prod_val else "⚠️ DIFFERENT"
            print(f"   {metric_name:20}: Original={orig_val}, Production={prod_val} ({status})")
        else:
            diff = abs(prod_val - orig_val) if isinstance(orig_val, (int, float)) and isinstance(prod_val, (int, float)) else "N/A"
            status = "✅ SAME" if orig_val == prod_val else f"📊 DIFF: {diff}"
            print(f"   {metric_name:20}: Original={orig_val}, Production={prod_val} ({status})")
    
    # Defensive patterns status
    print(f"\n🛡️ DEFENSIVE PATTERNS:")
    defensive_count = production_result.get("defensive_patterns_active", 0)
    print(f"   Active Patterns: {defensive_count}/6")
    
    # Quality assessment
    print(f"\n✅ QUALITY ASSESSMENT:")
    
    # Check if both systems produced meaningful results
    orig_meaningful = (original_result.get("flights_count", 0) > 0 and 
                      original_result.get("hotels_count", 0) > 0 and
                      original_result.get("final_plan_length", 0) > 100)
    
    prod_meaningful = (production_result.get("flights_count", 0) > 0 and 
                      production_result.get("hotels_count", 0) > 0 and
                      production_result.get("final_plan_length", 0) > 100)
    
    print(f"   Original System Quality:   {'✅ GOOD' if orig_meaningful else '⚠️ LIMITED'}")
    print(f"   Production System Quality: {'✅ GOOD' if prod_meaningful else '⚠️ LIMITED'}")
    
    # Overall assessment
    if orig_meaningful and prod_meaningful:
        if overhead < 50:  # Less than 50% overhead is acceptable
            print(f"\n🎉 OVERALL ASSESSMENT: ✅ PRODUCTION SYSTEM READY")
            print(f"   - Both systems produce quality results")
            print(f"   - Performance overhead is acceptable ({overhead:+.1f}%)")
            print(f"   - Defensive patterns provide additional reliability")
        else:
            print(f"\n⚠️ OVERALL ASSESSMENT: 🟡 NEEDS OPTIMIZATION")
            print(f"   - Both systems work but production has high overhead ({overhead:+.1f}%)")
    else:
        print(f"\n❌ OVERALL ASSESSMENT: 🔴 ISSUES DETECTED")
        print(f"   - One or both systems not producing quality results")

def main():
    """Main test function."""
    print("🧪 VACAYMATE SYSTEM COMPARISON TEST")
    print("📍 Route: Tel Aviv → Sofia")
    print("📅 Dates: 2025-10-10 to 2025-10-17")
    print("=" * 60)
    
    # Test original system
    original_result = test_original_system()
    
    # Test production system
    production_result = test_production_system()
    
    # Compare results
    compare_results(original_result, production_result)
    
    print(f"\n🏁 TEST COMPLETED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return original_result, production_result

if __name__ == "__main__":
    original_result, production_result = main()
