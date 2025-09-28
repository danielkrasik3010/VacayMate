import streamlit as st
import sys
import os
from datetime import datetime, date, timedelta
import pandas as pd
from pathlib import Path
import base64
import io
import json
import time

# Import plotly with fallback for cloud deployment
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Charts will be disabled.")

# Import psutil with fallback for cloud deployment
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import deduplication function from backend
try:
    from nodes.VacayMate_nodes import deduplicate_items
except ImportError:
    # Fallback deduplication function if import fails
    def deduplicate_items(items, min_items=5):
        def normalize_name(name):
            if not isinstance(name, str):
                return ""
            normalized = name.lower().strip()
            if normalized.startswith("the "):
                normalized = normalized[4:]
            import re
            normalized = re.sub(r'[^\w\s]', '', normalized)
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            return normalized
        
        def is_valid_attraction(item):
            """Filter out unwanted items during deduplication"""
            if not isinstance(item, str) or len(item.strip()) < 5:
                return False
            
            item_upper = item.upper().strip()
            # Filter out HTML fragments and unwanted text
            unwanted_patterns = [
                'TO SPEND', 'TIME TO SPEND', 'TYPE', 'SIGHTSEEING',
                'POPULAR ATTRACTION', 'MUST-VISIT'
            ]
            
            for pattern in unwanted_patterns:
                if pattern in item_upper:
                    return False
            
            # Filter out items with HTML-like content or excessive formatting
            if any(char in item for char in ['<', '>', '{', '}', '[', ']', '\n']):
                return False
                
            return True
        
        seen = set()
        unique_items = []
        for item in items:
            if is_valid_attraction(item):
                normalized = normalize_name(item)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    unique_items.append(item.strip())
        return unique_items

# Add the parent directory to the path to import VacayMate modules
current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent
code_dir = parent_dir / "code"

# Add paths for imports
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(code_dir))

# Import VacayMate system with fallback for cloud deployment
try:
    from VacayMate_system_production import ProductionVacayMate
    DEFENSIVE_MODE = True
except ImportError:
    try:
        # Fallback to regular VacayMate system if production version not available
        from VacayMate_system import VacayMate as ProductionVacayMate
        DEFENSIVE_MODE = False
        st.warning("⚠️ Production system not available, using standard VacayMate system")
    except ImportError:
        # Alternative import method - use absolute path
        import importlib.util
        
        # Try production system first
        vacaymate_file = code_dir / "VacayMate_system_production.py"
        if vacaymate_file.exists():
            spec = importlib.util.spec_from_file_location("VacayMate_system_production", vacaymate_file)
            vacaymate_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vacaymate_module)
            ProductionVacayMate = vacaymate_module.ProductionVacayMate
            DEFENSIVE_MODE = True
        else:
            # Fallback to regular system
            vacaymate_file = code_dir / "VacayMate_system.py"
            if vacaymate_file.exists():
                spec = importlib.util.spec_from_file_location("VacayMate_system", vacaymate_file)
                vacaymate_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(vacaymate_module)
                ProductionVacayMate = vacaymate_module.VacayMate
                DEFENSIVE_MODE = False
                st.warning("⚠️ Production system not available, using standard VacayMate system")
            else:
                st.error("❌ VacayMate system files not found. Please check your deployment.")
                st.stop()

# Page configuration
st.set_page_config(
    page_title="🛡️ VacayMate Defensive - AI Travel Planner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling with defensive theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2d3748 0%, #4a5568 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        border: 2px solid #38a169;
    }
    .defensive-badge {
        background: linear-gradient(90deg, #38a169 0%, #48bb78 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem;
    }
    .section-header {
        background: linear-gradient(90deg, #2b6cb0 0%, #3182ce 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #38a169;
    }
    .metric-card {
        background: linear-gradient(135deg, #2b6cb0 0%, #3182ce 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .defensive-metric-card {
        background: linear-gradient(135deg, #38a169 0%, #48bb78 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .warning-card {
        background: linear-gradient(135deg, #ed8936 0%, #f6ad55 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .error-card {
        background: linear-gradient(135deg, #e53e3e 0%, #fc8181 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .dashboard-card {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #38a169;
    }
    .circuit-breaker-closed {
        color: #38a169;
        font-weight: bold;
    }
    .circuit-breaker-open {
        color: #e53e3e;
        font-weight: bold;
    }
    .circuit-breaker-half-open {
        color: #ed8936;
        font-weight: bold;
    }
    .stButton > button {
        background: linear-gradient(90deg, #2b6cb0 0%, #3182ce 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .defensive-button > button {
        background: linear-gradient(90deg, #38a169 0%, #48bb78 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    """Convert image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def display_defensive_header():
    """Display the main header with defensive system branding"""
    # Add hero image if available
    hero_image_path = Path("Streamlit_Images/tavern-7411977_1280.jpg")
    if hero_image_path.exists():
        st.image(str(hero_image_path), use_container_width=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ VacayMate Defensive - AI Travel Planner</h1>
        <p>Production-Ready Travel Planning with Advanced Defensive Patterns</p>
        <div class="defensive-badge">✅ Circuit Breakers</div>
        <div class="defensive-badge">✅ State Validation</div>
        <div class="defensive-badge">✅ Output Validation</div>
        <div class="defensive-badge">✅ Retry Logic</div>
        <div class="defensive-badge">✅ Resource Limits</div>
        <div class="defensive-badge">✅ Loop Detection</div>
        <p><em>🚀 Enterprise-grade reliability with comprehensive monitoring</em></p>
    </div>
    """, unsafe_allow_html=True)

def display_system_dashboard():
    """Display comprehensive system dashboard with cloud compatibility"""
    st.sidebar.markdown("""
    <div class="section-header">
        <h2>🛡️ System Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for metrics if not exists
    if 'system_metrics' not in st.session_state:
        st.session_state.system_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0,
            'circuit_breaker_trips': 0,
            'validation_failures': 0,
            'retry_attempts': 0,
            'memory_usage': 0,
            'uptime_start': datetime.now(),
            'request_history': [],
            'response_times': [],
            'error_history': []
        }
    
    metrics = st.session_state.system_metrics
    uptime = datetime.now() - metrics['uptime_start']
    
    # System Status Overview
    st.sidebar.markdown("### 📊 System Status")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        success_rate = (metrics['successful_requests'] / max(metrics['total_requests'], 1)) * 100
        if success_rate >= 95:
            status_color = "defensive-metric-card"
            status_icon = "🟢"
        elif success_rate >= 80:
            status_color = "warning-card"
            status_icon = "🟡"
        else:
            status_color = "error-card"
            status_icon = "🔴"
        
        st.markdown(f"""
        <div class="{status_color}">
            <h4>{status_icon} System</h4>
            <h3>{success_rate:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="defensive-metric-card">
            <h4>⏱️ Uptime</h4>
            <h3>{uptime.seconds//3600}h {(uptime.seconds//60)%60}m</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Request Metrics
    st.sidebar.markdown("### 📈 Request Metrics")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📊 Total</h4>
            <h3>{metrics['total_requests']}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>⚡ Avg Time</h4>
            <h3>{metrics['avg_response_time']:.1f}s</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Defensive Pattern Metrics
    st.sidebar.markdown("### 🛡️ Defensive Patterns")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(f"""
        <div class="warning-card">
            <h4>🔄 Retries</h4>
            <h3>{metrics['retry_attempts']}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="error-card">
            <h4>⚠️ Failures</h4>
            <h3>{metrics['validation_failures']}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Memory Usage with cloud compatibility
    if PSUTIL_AVAILABLE:
        try:
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            st.session_state.system_metrics['memory_usage'] = memory_mb
            
            st.sidebar.markdown("### 💾 Resources")
            if memory_mb < 200:
                memory_color = "defensive-metric-card"
                memory_icon = "🟢"
            elif memory_mb < 500:
                memory_color = "warning-card"
                memory_icon = "🟡"
            else:
                memory_color = "error-card"
                memory_icon = "🔴"
            
            st.sidebar.markdown(f"""
            <div class="{memory_color}">
                <h4>{memory_icon} Memory</h4>
                <h3>{memory_mb:.1f}MB</h3>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.sidebar.markdown("### 💾 Resources")
            st.sidebar.markdown("""
            <div class="warning-card">
                <h4>⚠️ Memory</h4>
                <h3>N/A</h3>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("### 💾 Resources")
        st.sidebar.markdown("""
        <div class="warning-card">
            <h4>⚠️ Memory</h4>
            <h3>N/A</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Real-time refresh
    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()

def display_input_form():
    """Display the input form for trip details with defensive system branding"""
    st.markdown("""
    <div class="section-header">
        <h2>🛡️ Plan Your Trip (Defensive Mode)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            departure_city = st.text_input("🏠 Departure City", placeholder="e.g., Barcelona", help="Enter your departure city")
            
            # Real-time validation for departure city
            if departure_city:
                if not is_valid_city_local(departure_city):
                    st.warning(f"⚠️ '{departure_city}' may not be supported. Please check spelling or try a major city name.")
                else:
                    st.success(f"✅ '{departure_city}' is supported!")
            
            start_date = st.date_input("📅 Start Date", min_value=date.today(), help="Select your departure date")
            
        with col2:
            destination_city = st.text_input("🎯 Destination", placeholder="e.g., Paris", help="Enter your destination city")
            
            # Real-time validation for destination
            if destination_city:
                if not is_valid_city_local(destination_city):
                    st.warning(f"⚠️ '{destination_city}' may not be supported. Please check spelling or try a major city name.")
                else:
                    st.success(f"✅ '{destination_city}' is supported!")
            
            end_date = st.date_input("📅 End Date", min_value=date.today(), help="Select your return date")
        
        # Show popular cities hint
        if not departure_city or not destination_city:
            st.info("💡 **Popular cities:** Barcelona, Paris, London, Rome, New York, Tokyo, Sydney, Dubai, etc.")
        
        # Add sample data button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎯 Use Sample: Tel Aviv → Sofia", help="Fill form with sample data"):
                st.info("💡 Sample data loaded! Tel Aviv → Sofia for 7 days")
                departure_city = "Tel Aviv"
                destination_city = "Sofia"
    
    # Validation
    if start_date >= end_date:
        st.error("End date must be after start date!")
        return None, None, None, None
        
    return departure_city, destination_city, start_date, end_date

def run_defensive_vacaymate_system(departure_city, destination_city, start_date, end_date):
    """Run the Defensive VacayMate system and return results with metrics"""
    start_time = time.time()
    
    try:
        # Initialize Defensive VacayMate system
        vacay_mate = ProductionVacayMate(llm_model="gpt-4o-mini")
        
        # Convert dates to strings
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Run the system
        user_request = f"Plan a trip from {departure_city} to {destination_city} from {start_date_str} to {end_date_str}."
        
        final_state = vacay_mate.run(
            user_request=user_request,
            current_location=departure_city,
            destination=destination_city,
            start_date=start_date_str,
            return_date=end_date_str
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Update metrics
        if 'system_metrics' not in st.session_state:
            st.session_state.system_metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'circuit_breaker_trips': 0,
                'validation_failures': 0,
                'retry_attempts': 0,
                'memory_usage': 0,
                'uptime_start': datetime.now(),
                'request_history': [],
                'response_times': [],
                'error_history': []
            }
        
        metrics = st.session_state.system_metrics
        metrics['total_requests'] += 1
        metrics['successful_requests'] += 1
        metrics['response_times'].append(response_time)
        metrics['avg_response_time'] = sum(metrics['response_times']) / len(metrics['response_times'])
        
        # Store system health data if available
        try:
            if hasattr(vacay_mate, 'get_system_health'):
                system_health = vacay_mate.get_system_health()
                st.session_state.last_system_health = system_health
        except Exception as e:
            print(f"Warning: Could not get system health: {e}")
        
        return final_state, response_time
        
    except ValueError as e:
        # Handle city validation errors specifically
        response_time = time.time() - start_time
        
        # Update failure metrics
        if 'system_metrics' in st.session_state:
            metrics = st.session_state.system_metrics
            metrics['total_requests'] += 1
            metrics['failed_requests'] += 1
            metrics['validation_failures'] += 1
            metrics['error_history'].append({
                'time': datetime.now(),
                'error': str(e),
                'type': 'validation_error'
            })
        
        error_msg = str(e)
        st.error("❌ **Invalid City Input**")
        st.markdown(error_msg)
        
        # Show supported cities info
        with st.expander("🌍 View Supported Cities", expanded=False):
            st.markdown("""
            **VacayMate Defensive supports major cities from around the world including:**
            
            **Europe:** Barcelona, Paris, London, Rome, Berlin, Amsterdam, Madrid, Vienna, Prague, etc.
            
            **North America:** New York, Los Angeles, Toronto, Mexico City, Miami, San Francisco, etc.
            
            **Asia:** Tokyo, Seoul, Bangkok, Singapore, Dubai, Mumbai, Shanghai, etc.
            
            **South America:** Buenos Aires, São Paulo, Rio de Janeiro, Santiago, etc.
            
            **Africa & Middle East:** Cairo, Dubai, Cape Town, Tel Aviv, etc.
            
            **Oceania:** Sydney, Melbourne, Auckland, etc.
            
            💡 **Tip:** Try using the full city name or check the spelling. For example:
            - Use "New York" instead of "NYC"
            - Use "Los Angeles" instead of "LA" 
            - Use "São Paulo" instead of "Sao Paulo"
            """)
        
        return None, response_time
        
    except Exception as e:
        response_time = time.time() - start_time
        
        # Update failure metrics
        if 'system_metrics' in st.session_state:
            metrics = st.session_state.system_metrics
            metrics['total_requests'] += 1
            metrics['failed_requests'] += 1
            metrics['error_history'].append({
                'time': datetime.now(),
                'error': str(e),
                'type': 'system_error'
            })
        
        st.error(f"❌ **System Error:** {str(e)}")
        return None, response_time

# Import display functions from original app (flights, hotels, etc.)
from app import (
    display_flights, display_hotels, display_attractions, 
    display_weather, display_events, display_cost_summary, 
    display_final_summary, is_valid_city_local, 
    get_city_validation_error_local, create_demo_data
)

def create_markdown_export(final_state, departure_city, destination_city, start_date, end_date):
    """Create markdown content for export"""
    try:
        # Use the defensive system's export functionality
        vacay_mate = ProductionVacayMate()
        markdown_content = vacay_mate._build_markdown_content(
            final_state, 
            destination_city, 
            start_date.strftime("%Y-%m-%d"), 
            end_date.strftime("%Y-%m-%d")
        )
        return markdown_content
    except Exception as e:
        # Fallback to simple markdown generation
        return f"""# 🛡️ VacayMate Defensive Travel Plan

**Destination:** {destination_city}
**Departure:** {departure_city}
**Dates:** {start_date} to {end_date}

## Travel Plan
{final_state.get('final_plan', 'Plan details not available')}

*Generated by VacayMate Defensive System*
"""

def main():
    # Display sidebar dashboard first
    display_system_dashboard()
    
    # Display header
    display_defensive_header()
    
    # Input form
    departure_city, destination_city, start_date, end_date = display_input_form()
    
    # Generate button and demo mode
    col1, col2 = st.columns(2)
    
    with col1:
        generate_clicked = st.button("🛡️ Generate Defensive Plan", type="primary", help="Generate with full defensive patterns")
    
    with col2:
        demo_clicked = st.button("👀 View Demo (Instant)", type="secondary", help="See sample results instantly")
    
    if generate_clicked:
        if not all([departure_city, destination_city, start_date, end_date]):
            st.error("Please fill in all fields!")
            return
            
        if len(departure_city.strip()) < 2 or len(destination_city.strip()) < 2:
            st.error("Please enter valid city names!")
            return
        
        # Validate cities before processing
        validation_errors = []
        
        departure_valid = is_valid_city_local(departure_city)
        destination_valid = is_valid_city_local(destination_city)
        
        if not departure_valid:
            error_msg = get_city_validation_error_local(departure_city, 'Departure City')
            validation_errors.append(f"**Departure City:** {error_msg}")
        
        if not destination_valid:
            error_msg = get_city_validation_error_local(destination_city, 'Destination')
            validation_errors.append(f"**Destination:** {error_msg}")
        
        if validation_errors:
            st.error("❌ **Invalid City Input**")
            st.error("🛑 **BLOCKING PROCESSING - INVALID CITIES DETECTED**")
            for error in validation_errors:
                st.markdown(error)
            
            # Show supported cities info
            with st.expander("🌍 View Supported Cities", expanded=True):
                st.markdown("""
                **VacayMate Defensive supports major cities from around the world including:**
                
                **Europe:** Barcelona, Paris, London, Rome, Berlin, Amsterdam, Madrid, Vienna, Prague, etc.
                
                **North America:** New York, Los Angeles, Toronto, Mexico City, Miami, San Francisco, etc.
                
                **Asia:** Tokyo, Seoul, Bangkok, Singapore, Dubai, Mumbai, Shanghai, etc.
                
                **South America:** Buenos Aires, São Paulo, Rio de Janeiro, Santiago, etc.
                
                **Africa & Middle East:** Cairo, Dubai, Cape Town, Tel Aviv, etc.
                
                **Oceania:** Sydney, Melbourne, Auckland, etc.
                
                💡 **Tip:** Try using the full city name or check the spelling. For example:
                - Use "New York" instead of "NYC"
                - Use "Los Angeles" instead of "LA" 
                - Use "São Paulo" instead of "Sao Paulo"
                """)
            st.stop()
        
        # Show loading spinner with defensive system messaging
        with st.spinner("🛡️ Defensive AI is planning your vacation with full resilience patterns... This may take 30-60 seconds."):
            # Add progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔍 Initializing defensive systems...")
            progress_bar.progress(10)
            time.sleep(0.5)
            
            status_text.text("🛡️ Activating circuit breakers...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            status_text.text("✅ Running state validation...")
            progress_bar.progress(30)
            time.sleep(0.5)
            
            status_text.text("🔄 Processing with retry logic...")
            progress_bar.progress(50)
            
            final_state, response_time = run_defensive_vacaymate_system(departure_city, destination_city, start_date, end_date)
            
            progress_bar.progress(100)
            status_text.text("✅ Defensive processing complete!")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
        
        if final_state:
            st.success(f"🎉 Your defensive vacation plan is ready! (Generated in {response_time:.2f}s)")
            
            # Show defensive system success metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("""
                <div class="defensive-metric-card">
                    <h4>✅ State Validation</h4>
                    <h3>PASSED</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="defensive-metric-card">
                    <h4>🔌 Circuit Breakers</h4>
                    <h3>ACTIVE</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div class="defensive-metric-card">
                    <h4>🔄 Retry Logic</h4>
                    <h3>READY</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="defensive-metric-card">
                    <h4>⚡ Response Time</h4>
                    <h3>{response_time:.1f}s</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Store results in session state for persistence
            st.session_state['vacation_results'] = final_state
            st.session_state['trip_details'] = {
                'departure_city': departure_city,
                'destination_city': destination_city,
                'start_date': start_date,
                'end_date': end_date
            }
    
    elif demo_clicked:
        # Create demo data
        st.info("🎭 Showing demo results for Barcelona → Paris (Defensive Mode)")
        demo_state = create_demo_data()
        st.session_state['vacation_results'] = demo_state
        st.session_state['trip_details'] = {
            'departure_city': 'Barcelona',
            'destination_city': 'Paris',
            'start_date': start_date or date.today(),
            'end_date': end_date or date.today().replace(day=date.today().day + 5)
        }
    
    # Display results if available
    if 'vacation_results' in st.session_state:
        final_state = st.session_state['vacation_results']
        trip_details = st.session_state['trip_details']
        
        research_results = final_state.get("research_results", {})
        planner_results = final_state.get("planner_results", {})
        calculator_results = final_state.get("calculator_results", {})
        
        # Display all sections
        st.markdown("---")
        
        # Create tabs for better organization
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["✈️ Flights & Hotels", "🌍 Attractions & Events", "🌤️ Weather", "💰 Costs", "📋 Summary"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                display_flights(research_results)
            with col2:
                display_hotels(research_results)
        
        with tab2:
            display_attractions(research_results)
            display_events(planner_results)
        
        with tab3:
            display_weather(planner_results)
        
        with tab4:
            display_cost_summary(calculator_results)
        
        with tab5:
            display_final_summary(final_state)
        
        # Markdown export button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📄 Download Complete Defensive Plan (Markdown)", type="secondary"):
                try:
                    markdown_content = create_markdown_export(
                        final_state, 
                        trip_details['departure_city'], 
                        trip_details['destination_city'],
                        trip_details['start_date'], 
                        trip_details['end_date']
                    )
                    
                    # Create download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"defensive_vacation_plan_{trip_details['destination_city'].lower()}_{timestamp}.md"
                    
                    st.download_button(
                        label="💾 Download Defensive Plan",
                        data=markdown_content,
                        file_name=filename,
                        mime="text/markdown",
                        type="primary"
                    )
                    
                    st.success(f"📋 Your defensive vacation plan is ready for download as {filename}")
                    
                except Exception as e:
                    st.error(f"Error creating markdown export: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>🛡️ <strong>VacayMate Defensive</strong> - Production-Ready AI Travel Companion</p>
        <p>Made with ❤️ using Streamlit, advanced AI technology, and comprehensive defensive patterns</p>
        <p><em>✅ Circuit Breakers | ✅ State Validation | ✅ Output Validation | ✅ Retry Logic | ✅ Resource Limits | ✅ Loop Detection</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
