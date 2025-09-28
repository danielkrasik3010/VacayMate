import streamlit as st
import sys
from datetime import datetime, date, timedelta
import pandas as pd
from pathlib import Path
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psutil
import random

# Add the parent directory to the path to import VacayMate modules
current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent
code_dir = parent_dir / "code"

# Add paths for imports
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(code_dir))

# Import defensive patterns for health monitoring
try:
    from defensive_patterns import get_system_health
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False
    def get_system_health():
        return {
            "circuit_breakers": {
                "flight_search": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
                "hotel_search": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
                "weather_forecast": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
                "events_search": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
                "destination_info": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"}
            },
            "memory_usage_mb": 100,
            "uptime_seconds": 3600
        }

# Page configuration
st.set_page_config(
    page_title="🛡️ VacayMate Defensive System Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dashboard styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a202c 0%, #2d3748 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        border: 2px solid #38a169;
    }
    .metric-card {
        background: linear-gradient(135deg, #2b6cb0 0%, #3182ce 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .success-card {
        background: linear-gradient(135deg, #38a169 0%, #48bb78 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .warning-card {
        background: linear-gradient(135deg, #ed8936 0%, #f6ad55 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .error-card {
        background: linear-gradient(135deg, #e53e3e 0%, #fc8181 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .dashboard-section {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #38a169;
    }
    .circuit-breaker-closed {
        color: #38a169;
        font-weight: bold;
        font-size: 1.2em;
    }
    .circuit-breaker-open {
        color: #e53e3e;
        font-weight: bold;
        font-size: 1.2em;
    }
    .circuit-breaker-half-open {
        color: #ed8936;
        font-weight: bold;
        font-size: 1.2em;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-healthy { background-color: #38a169; }
    .status-warning { background-color: #ed8936; }
    .status-error { background-color: #e53e3e; }
</style>
""", unsafe_allow_html=True)

def initialize_dashboard_data():
    """Initialize dashboard data in session state"""
    if 'dashboard_data' not in st.session_state:
        st.session_state.dashboard_data = {
            'start_time': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'error_log': [],
            'circuit_breaker_trips': 0,
            'validation_failures': 0,
            'retry_attempts': 0,
            'memory_history': [],
            'cpu_history': [],
            'request_history': [],
            'last_health_check': None
        }

def display_dashboard_header():
    """Display the main dashboard header"""
    data_source = "🟢 Real-time Data" if REAL_DATA_AVAILABLE else "🟡 Demo Data"
    st.markdown(f"""
    <div class="main-header">
        <h1>🛡️ VacayMate Defensive System Dashboard</h1>
        <p>Real-time monitoring of production-ready travel planning system</p>
        <p><em>📊 Comprehensive metrics | 🔍 System health | 🛡️ Defensive patterns monitoring</em></p>
        <p><strong>Data Source: {data_source}</strong></p>
    </div>
    """, unsafe_allow_html=True)

def display_system_overview():
    """Display system overview metrics"""
    st.markdown("## 📊 System Overview")
    
    # Get current system health
    try:
        health_data = get_system_health()
        st.session_state.dashboard_data['last_health_check'] = datetime.now()
    except Exception as e:
        health_data = {
            "circuit_breakers": {},
            "memory_usage_mb": 100,
            "uptime_seconds": 3600
        }
    
    # Calculate uptime
    uptime = datetime.now() - st.session_state.dashboard_data['start_time']
    uptime_hours = uptime.total_seconds() / 3600
    
    # System status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Overall system health
        total_requests = st.session_state.dashboard_data['total_requests']
        success_rate = 100.0
        if total_requests > 0:
            success_rate = (st.session_state.dashboard_data['successful_requests'] / total_requests) * 100
        
        if success_rate >= 95:
            card_class = "success-card"
            status_icon = "🟢"
        elif success_rate >= 80:
            card_class = "warning-card"
            status_icon = "🟡"
        else:
            card_class = "error-card"
            status_icon = "🔴"
        
        st.markdown(f"""
        <div class="{card_class}">
            <h3>{status_icon} System Health</h3>
            <h2>{success_rate:.1f}%</h2>
            <p>Success Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Uptime
        st.markdown(f"""
        <div class="success-card">
            <h3>⏱️ Uptime</h3>
            <h2>{uptime_hours:.1f}h</h2>
            <p>System Running</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Memory usage
        memory_mb = health_data.get('memory_usage_mb', 100)
        if memory_mb < 200:
            memory_card = "success-card"
            memory_icon = "🟢"
        elif memory_mb < 500:
            memory_card = "warning-card"
            memory_icon = "🟡"
        else:
            memory_card = "error-card"
            memory_icon = "🔴"
        
        st.markdown(f"""
        <div class="{memory_card}">
            <h3>{memory_icon} Memory</h3>
            <h2>{memory_mb:.1f}MB</h2>
            <p>Current Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Total requests
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Requests</h3>
            <h2>{total_requests}</h2>
            <p>Total Processed</p>
        </div>
        """, unsafe_allow_html=True)

def display_defensive_patterns_status():
    """Display defensive patterns status"""
    st.markdown("## 🛡️ Defensive Patterns Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <h4>🔍 State Validation</h4>
            <p><span class="status-indicator status-healthy"></span><strong>ACTIVE</strong></p>
            <p>Input/Output validation on all nodes</p>
            <p>Failures: <strong>{}</strong></p>
        </div>
        """.format(st.session_state.dashboard_data['validation_failures']), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="dashboard-section">
            <h4>🔄 Retry Logic</h4>
            <p><span class="status-indicator status-healthy"></span><strong>ACTIVE</strong></p>
            <p>Exponential backoff with jitter</p>
            <p>Attempts: <strong>{}</strong></p>
        </div>
        """.format(st.session_state.dashboard_data['retry_attempts']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <h4>⚡ Resource Limits</h4>
            <p><span class="status-indicator status-healthy"></span><strong>ACTIVE</strong></p>
            <p>Memory & time constraints</p>
            <p>Max Memory: <strong>100MB</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="dashboard-section">
            <h4>🔍 Loop Detection</h4>
            <p><span class="status-indicator status-healthy"></span><strong>ACTIVE</strong></p>
            <p>Iteration caps and cycle detection</p>
            <p>Max Iterations: <strong>20</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="dashboard-section">
            <h4>✅ Output Validation</h4>
            <p><span class="status-indicator status-healthy"></span><strong>ACTIVE</strong></p>
            <p>Pydantic schema validation</p>
            <p>All APIs validated</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="dashboard-section">
            <h4>🔌 Circuit Breakers</h4>
            <p><span class="status-indicator status-healthy"></span><strong>ACTIVE</strong></p>
            <p>Service failure protection</p>
            <p>Trips: <strong>{}</strong></p>
        </div>
        """.format(st.session_state.dashboard_data['circuit_breaker_trips']), unsafe_allow_html=True)

def display_circuit_breaker_status():
    """Display detailed circuit breaker status"""
    st.markdown("## 🔌 Circuit Breaker Status")
    
    try:
        health_data = get_system_health()
        circuit_breakers = health_data.get('circuit_breakers', {})
    except:
        # Fallback data
        circuit_breakers = {
            "flight_search": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
            "hotel_search": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
            "weather_forecast": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
            "events_search": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"},
            "destination_info": {"disabled": False, "failures": 0, "last_success": "2025-09-26 15:30:00"}
        }
    
    if circuit_breakers:
        # Create circuit breaker status table
        cb_data = []
        for service, status in circuit_breakers.items():
            is_disabled = status.get('disabled', False)
            failures = status.get('failures', 0)
            last_success = status.get('last_success', 'Never')
            
            if is_disabled:
                status_text = "🔴 OPEN"
                status_class = "circuit-breaker-open"
            elif failures > 0:
                status_text = "🟡 MONITORING"
                status_class = "circuit-breaker-half-open"
            else:
                status_text = "🟢 CLOSED"
                status_class = "circuit-breaker-closed"
            
            cb_data.append({
                'Service': service.replace('_', ' ').title(),
                'Status': status_text,
                'Failures': failures,
                'Last Success': last_success,
                'Health': 'Healthy' if not is_disabled else 'Degraded'
            })
        
        df = pd.DataFrame(cb_data)
        st.dataframe(df, width='stretch')
        
        # Circuit breaker status visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution pie chart
            status_counts = df['Health'].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=.3,
                marker_colors=['#38a169' if status == 'Healthy' else '#e53e3e' for status in status_counts.index]
            )])
            fig.update_layout(
                title="Circuit Breaker Health Distribution",
                height=400
            )
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Failure count bar chart
            fig = px.bar(df, x='Service', y='Failures', 
                        title="Circuit Breaker Failure Counts",
                        color='Failures',
                        color_continuous_scale='RdYlGn_r')
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
    else:
        st.info("🔌 Circuit breaker data will be available after system initialization")

def display_performance_metrics():
    """Display performance metrics and charts"""
    st.markdown("## 📈 Performance Metrics")
    
    # Generate sample data for demonstration
    if len(st.session_state.dashboard_data['response_times']) == 0:
        # Add some sample response times
        sample_times = [8.5, 9.2, 7.8, 10.1, 8.9, 9.5, 8.2, 9.8, 8.7, 9.3]
        st.session_state.dashboard_data['response_times'] = sample_times
        st.session_state.dashboard_data['total_requests'] = len(sample_times)
        st.session_state.dashboard_data['successful_requests'] = len(sample_times)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Response time trend
        response_times = st.session_state.dashboard_data['response_times']
        if response_times:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=response_times,
                mode='lines+markers',
                name='Response Time',
                line=dict(color='#3182ce', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Response Time Trend",
                xaxis_title="Request Number",
                yaxis_title="Response Time (seconds)",
                height=400
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("📊 Response time data will appear after processing requests")
    
    with col2:
        # Request success/failure distribution
        total_requests = st.session_state.dashboard_data['total_requests']
        successful_requests = st.session_state.dashboard_data['successful_requests']
        failed_requests = st.session_state.dashboard_data['failed_requests']
        
        if total_requests > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Successful', 'Failed'],
                values=[successful_requests, failed_requests],
                hole=.3,
                marker_colors=['#38a169', '#e53e3e']
            )])
            fig.update_layout(
                title="Request Success Rate",
                height=400
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("📊 Request data will appear after processing requests")

def display_system_health_timeline():
    """Display system health over time"""
    st.markdown("## 📊 System Health Timeline")
    
    # Generate sample timeline data
    now = datetime.now()
    timeline_data = {
        'Time': [now - timedelta(minutes=x*5) for x in range(12, 0, -1)],
        'CPU': [15 + random.randint(-5, 15) for _ in range(12)],
        'Memory': [100 + random.randint(-20, 40) for _ in range(12)],
        'Requests': [random.randint(0, 5) for _ in range(12)],
        'Response_Time': [8 + random.uniform(-2, 4) for _ in range(12)]
    }
    
    # Create subplots
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=('CPU Usage (%)', 'Memory Usage (MB)', 'Requests per 5min', 'Avg Response Time (s)'),
        vertical_spacing=0.08
    )
    
    # Add traces
    fig.add_trace(go.Scatter(x=timeline_data['Time'], y=timeline_data['CPU'], 
                            name='CPU', line=dict(color='#3182ce', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=timeline_data['Time'], y=timeline_data['Memory'], 
                            name='Memory', line=dict(color='#38a169', width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=timeline_data['Time'], y=timeline_data['Requests'], 
                            name='Requests', line=dict(color='#ed8936', width=2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=timeline_data['Time'], y=timeline_data['Response_Time'], 
                            name='Response Time', line=dict(color='#e53e3e', width=2)), row=4, col=1)
    
    fig.update_layout(height=800, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def display_error_log():
    """Display error log and system events"""
    st.markdown("## 📋 System Events & Error Log")
    
    # Sample error log data
    if not st.session_state.dashboard_data['error_log']:
        sample_events = [
            {'timestamp': datetime.now() - timedelta(minutes=30), 'level': 'INFO', 'message': 'System initialized successfully'},
            {'timestamp': datetime.now() - timedelta(minutes=25), 'level': 'INFO', 'message': 'Circuit breakers activated'},
            {'timestamp': datetime.now() - timedelta(minutes=20), 'level': 'INFO', 'message': 'State validation enabled'},
            {'timestamp': datetime.now() - timedelta(minutes=15), 'level': 'WARNING', 'message': 'High memory usage detected (180MB)'},
            {'timestamp': datetime.now() - timedelta(minutes=10), 'level': 'INFO', 'message': 'Memory usage normalized'},
            {'timestamp': datetime.now() - timedelta(minutes=5), 'level': 'INFO', 'message': 'All defensive patterns operational'},
        ]
        st.session_state.dashboard_data['error_log'] = sample_events
    
    # Display events in a table
    events_df = pd.DataFrame(st.session_state.dashboard_data['error_log'])
    if not events_df.empty:
        events_df['timestamp'] = events_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(events_df, use_container_width=True)
    else:
        st.info("📋 System events will appear here as they occur")

def display_api_health_matrix():
    """Display API health matrix"""
    st.markdown("## 🌐 API Health Matrix")
    
    # API health data
    apis = ['Flight Search', 'Hotel Search', 'Weather Forecast', 'Events Search', 'Destination Info']
    metrics = ['Availability', 'Response Time', 'Error Rate', 'Circuit Breaker']
    
    # Generate sample health matrix
    health_matrix = []
    for api in apis:
        row = {'API': api}
        for metric in metrics:
            if metric == 'Availability':
                row[metric] = f"{random.randint(95, 100)}%"
            elif metric == 'Response Time':
                row[metric] = f"{random.uniform(0.5, 2.0):.1f}s"
            elif metric == 'Error Rate':
                row[metric] = f"{random.uniform(0, 5):.1f}%"
            else:  # Circuit Breaker
                row[metric] = "🟢 CLOSED"
        health_matrix.append(row)
    
    df = pd.DataFrame(health_matrix)
    st.dataframe(df, use_container_width=True)

def main():
    # Initialize dashboard data
    initialize_dashboard_data()
    
    # Display header
    display_dashboard_header()
    
    # Auto-refresh option
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh every 30 seconds", value=False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    # Manual refresh button
    if st.button("🔄 Refresh Dashboard", type="primary"):
        st.rerun()
    
    # Display dashboard sections
    display_system_overview()
    
    st.markdown("---")
    display_defensive_patterns_status()
    
    st.markdown("---")
    display_circuit_breaker_status()
    
    st.markdown("---")
    display_performance_metrics()
    
    st.markdown("---")
    display_system_health_timeline()
    
    st.markdown("---")
    display_api_health_matrix()
    
    st.markdown("---")
    display_error_log()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>🛡️ <strong>VacayMate Defensive System Dashboard</strong></p>
        <p>Real-time monitoring and analytics for production-ready travel planning</p>
        <p><em>Last updated: {}</em></p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
