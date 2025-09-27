#!/usr/bin/env python3
"""
Simple test script for LangSmith tracing with environment variable loading.
"""

import os
import sys

# Load environment variables from .env file if it exists
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
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
                    print(f"  ✅ {key} = {value[:20]}..." if len(value) > 20 else f"  ✅ {key} = {value}")
    else:
        print(f"⚠️ No .env file found at {env_file}")

# Load environment variables
load_env_file()

# Add code directory to path
sys.path.insert(0, 'code')

def test_simple_tracing():
    """Test simple LangSmith tracing."""
    print("\n🔍 Testing LangSmith Integration")
    print("=" * 40)
    
    # Check if tracing is enabled
    tracing_enabled = os.getenv("LANGSMITH_TRACING") == "True"
    print(f"🔍 Tracing enabled: {tracing_enabled}")
    
    if not tracing_enabled:
        print("⚠️ LangSmith tracing is disabled. Set LANGSMITH_TRACING=True to enable.")
        return False
    
    # Test import
    try:
        from VacayMate_system_production import ProductionVacayMate
        print("✅ ProductionVacayMate imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Initialize system
    try:
        system = ProductionVacayMate(max_iterations=5, enable_monitoring=True)
        print(f"✅ System initialized (Session: {system.session_id})")
        print(f"🔍 Tracing enabled: {system.tracing_enabled}")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False
    
    # Test a simple health check
    try:
        health = system.get_system_health()
        print(f"✅ Health check completed")
        print(f"📊 Memory usage: {health.get('memory_usage_mb', 0):.1f}MB")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    print("\n🎉 Simple test completed successfully!")
    print("🔗 Check your LangSmith dashboard for traces")
    return True

if __name__ == "__main__":
    success = test_simple_tracing()
    sys.exit(0 if success else 1)
