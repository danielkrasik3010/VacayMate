import streamlit as st
import sys
import os
from datetime import datetime, date
import pandas as pd
from pathlib import Path
import base64
import io

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

# Import VacayMate system
try:
    from VacayMate_system import VacayMate
except ImportError:
    # Alternative import method - use absolute path
    import importlib.util
    vacaymate_file = code_dir / "VacayMate_system.py"
    vacaymate_file = vacaymate_file.resolve()  # Get absolute path
    
    # Debug: Print the path being used
    print(f"Looking for VacayMate_system.py at: {vacaymate_file}")
    print(f"File exists: {vacaymate_file.exists()}")
    
    if not vacaymate_file.exists():
        st.error(f"VacayMate_system.py not found at: {vacaymate_file}")
        st.stop()
    
    spec = importlib.util.spec_from_file_location("VacayMate_system", vacaymate_file)
    vacaymate_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vacaymate_module)
    VacayMate = vacaymate_module.VacayMate

# Page configuration
st.set_page_config(
    page_title="VacayMate - AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .section-header {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
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
        border-left: 4px solid #667eea;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .flight-table, .hotel-table {
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .weather-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .event-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #fd79a8;
    }
    .attraction-card {
        background: #fff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #00b894;
    }
    .summary-card {
        background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    """Convert image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def display_header():
    """Display the main header with background image"""
    # Add hero image if available
    hero_image_path = Path("Streamlit_Images/tavern-7411977_1280.jpg")
    if hero_image_path.exists():
        st.image(str(hero_image_path), use_container_width=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🌍 VacayMate - AI Travel Planner</h1>
        <p>Plan your perfect vacation with AI-powered recommendations</p>
        <p><em>✨ Discover flights, hotels, attractions, weather, and events - all in one place!</em></p>
    </div>
    """, unsafe_allow_html=True)

def display_input_form():
    """Display the input form for trip details"""
    st.markdown("""
    <div class="section-header">
        <h2>✈️ Plan Your Trip</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # City validation is now handled by local functions
    
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
            if st.button("🎯 Use Sample: Barcelona → Paris", help="Fill form with sample data"):
                st.info("💡 Sample data loaded! Barcelona → Paris for 5 days")
                departure_city = "Barcelona"
                destination_city = "Paris"
                # Use default dates if sample button clicked
                if not departure_city:
                    departure_city = "Barcelona"
                if not destination_city:
                    destination_city = "Paris"
    
    # Validation
    if start_date >= end_date:
        st.error("End date must be after start date!")
        return None, None, None, None
        
    return departure_city, destination_city, start_date, end_date

def run_vacaymate_system(departure_city, destination_city, start_date, end_date):
    """Run the VacayMate system and return results"""
    try:
        # Initialize VacayMate system
        vacay_mate = VacayMate(llm_model="gpt-4o-mini")
        
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
        
        return final_state
        
    except ValueError as e:
        # Handle city validation errors specifically
        error_msg = str(e)
        st.error("❌ **Invalid City Input**")
        st.markdown(error_msg)
        
        # Show supported cities info
        with st.expander("🌍 View Supported Cities", expanded=False):
            st.markdown("""
            **VacayMate supports major cities from around the world including:**
            
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
        
        return None
        
    except Exception as e:
        st.error(f"❌ **System Error:** {str(e)}")
        return None

def display_flights(research_results):
    """Display flight options in a beautiful table"""
    st.markdown("""
    <div class="section-header">
        <h2>✈️ Flight Options</h2>
    </div>
    """, unsafe_allow_html=True)
    
    flights = research_results.get("flights", [])
    if flights:
        # Create DataFrame for better display
        flight_data = []
        for flight in flights[:5]:  # Show top 5 flights
            # Get outbound and inbound details
            outbound = flight.get("outbound", {})
            inbound = flight.get("inbound", {})
            
            flight_data.append({
                "Airline": flight.get("airline", "N/A"),
                "Flight No.": flight.get("flightNumber", "N/A"),
                "Route": f"{flight.get('departureAirport', 'N/A')} → {flight.get('arrivalAirport', 'N/A')}",
                "Departure": flight.get("departureTime", "N/A"),
                "Arrival": flight.get("arrivalTime", "N/A"),
                "Duration Out": flight.get("durationOutbound", "N/A"),
                "Duration Return": flight.get("durationInbound", "N/A"),
                "Cabin Class": outbound.get("cabinClass", "Economy"),
                "Seats Left": flight.get("lastAvailableSeats", "N/A"),
                "Price USD": f"${flight.get('priceUSD', 0):.2f}",
                "Price EUR": f"€{flight.get('priceEUR', 0):.2f}"
            })
        
        df = pd.DataFrame(flight_data)
        st.dataframe(df, use_container_width=True)
        
        # Highlight best option
        if flight_data:
            best_flight = flight_data[0]
            # Get additional details from the original flight object
            best_flight_obj = flights[0]
            outbound = best_flight_obj.get("outbound", {})
            inbound = best_flight_obj.get("inbound", {})
            
            st.markdown(f"""
            <div class="card">
                <h4>🌟 Recommended Flight</h4>
                <p><strong>{best_flight['Airline']}</strong> - {best_flight['Flight No.']}</p>
                <p>🛫 <strong>Outbound:</strong> {best_flight['Departure']} → {best_flight['Arrival']} ({best_flight['Duration Out']})</p>
                {f'<p>🛬 <strong>Return:</strong> {inbound.get("departureLocalTime", "N/A")} → {inbound.get("arrivalLocalTime", "N/A")} ({best_flight["Duration Return"]})</p>' if inbound.get("departureLocalTime") else ''}
                <p>✈️ <strong>Route:</strong> {best_flight['Route']}</p>
                <p>🎫 <strong>Class:</strong> {best_flight['Cabin Class']} | <strong>Seats Left:</strong> {best_flight['Seats Left']}</p>
                <p>💰 <strong>Price:</strong> {best_flight['Price USD']} / {best_flight['Price EUR']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No flight options found.")

def display_hotels(research_results):
    """Display hotel options in a beautiful table"""
    st.markdown("""
    <div class="section-header">
        <h2>🏨 Hotel Options</h2>
    </div>
    """, unsafe_allow_html=True)
    
    accommodations = research_results.get("accommodations", {})
    hotels = accommodations.get("hotels", []) if isinstance(accommodations, dict) else []
    
    if hotels:
        # Create DataFrame for better display
        hotel_data = []
        for hotel in hotels[:5]:  # Show top 5 hotels
            price = hotel.get("price", {})
            per_night = price.get("per_night", "N/A") if isinstance(price, dict) else "N/A"
            total_price = price.get("total", "N/A") if isinstance(price, dict) else "N/A"
            
            # Get address and coordinates
            address_info = hotel.get("address", {})
            if isinstance(address_info, dict):
                formatted_address = address_info.get("formatted", "N/A")
                coordinates = address_info.get("coordinates", {})
                lat = coordinates.get("latitude") if isinstance(coordinates, dict) else None
                lng = coordinates.get("longitude") if isinstance(coordinates, dict) else None
                coord_str = f"{lat:.4f}, {lng:.4f}" if lat and lng else "N/A"
            else:
                formatted_address = "N/A"
                coord_str = "N/A"
            
            hotel_data.append({
                "Hotel": hotel.get("name", "N/A"),
                "Class": f"{hotel.get('hotel_class', 'N/A')}⭐" if hotel.get('hotel_class') else "N/A",
                "Price/Night": per_night,
                "Total Price": total_price,
                "Rating": f"{hotel.get('rating', 'N/A')}⭐" if hotel.get('rating') else "N/A",
                "Address": formatted_address,
                "Coordinates": coord_str,
                "Amenities": hotel.get("amenities", "N/A")
            })
        
        df = pd.DataFrame(hotel_data)
        st.dataframe(df, use_container_width=True)
        
        # Highlight best option
        if hotel_data:
            best_hotel = hotel_data[0]
            # Get additional info from the original hotel object
            best_hotel_obj = hotels[0]
            booking_link = best_hotel_obj.get("booking_link", "")
            description = best_hotel_obj.get("description", "")
            check_in = best_hotel_obj.get("check_in", "")
            check_out = best_hotel_obj.get("check_out", "")
            
            st.markdown(f"""
            <div class="card">
                <h4>🌟 Recommended Hotel</h4>
                <p><strong>{best_hotel['Hotel']}</strong> {best_hotel['Class']}</p>
                <p>💰 <strong>{best_hotel['Price/Night']}</strong> per night | Total: <strong>{best_hotel['Total Price']}</strong></p>
                <p>⭐ Rating: {best_hotel['Rating']}</p>
                <p>📍 {best_hotel['Address']}</p>
                <p>🌐 Coordinates: {best_hotel['Coordinates']}</p>
                <p>🛎️ {best_hotel['Amenities']}</p>
                {f'<p>🕐 Check-in: {check_in} | Check-out: {check_out}</p>' if check_in and check_out else ''}
                {f'<p>📝 {description[:150]}...</p>' if description and len(description) > 10 else ''}
                {f'<p><a href="{booking_link}" target="_blank" style="color: #667eea;">🔗 Book Now</a></p>' if booking_link else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No hotel options found.")

def display_attractions(research_results):
    """Display top attractions"""
    st.markdown("""
    <div class="section-header">
        <h2>🌍 Top Attractions</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Extract attractions from destination_info research
    destination_info = research_results.get("destination_info", [])
    attractions_found = False
    
    if isinstance(destination_info, list) and destination_info:
        # Try to extract attraction information from the researched content
        for source in destination_info:
            if isinstance(source, dict) and "content" in source:
                content = source.get("content", "")
                if content and len(content) > 100:  # Has substantial content
                    # Parse attractions from the content
                    import re
                    
                    # Extract attraction names from various patterns - improved to avoid HTML fragments
                    attraction_patterns = [
                        r'\b(?:St\.|Saint)\s+[A-Z][a-zA-Z\s]{3,25}(?:Cathedral|Church)\b',  # Churches/Cathedrals
                        r'\b[A-Z][a-zA-Z\s]{3,25}(?:Museum|Gallery)\b',  # Museums
                        r'\b[A-Z][a-zA-Z\s]{3,25}(?:Boulevard|Street|Square|Platz)\b',  # Streets/Squares
                        r'\b[A-Z][a-zA-Z\s]{3,25}(?:Monastery|Fortress|Palace|Castle)\b',  # Historic sites
                        r'\bMount\s+[A-Z][a-zA-Z]{3,15}\b',  # Mountains
                        r'\b[A-Z][a-zA-Z\s]{3,25}(?:Park|Garden)\b',  # Parks
                        r'\b[A-Z][a-zA-Z\s]{3,25}(?:Tower|Bridge|Gate|Wall)\b',  # Landmarks
                        r'\bBrandenburg\s+Gate\b',  # Specific Berlin attractions
                        r'\bEast\s+Side\s+Gallery\b',  # Specific Berlin attractions
                        r'\bBerlin\s+Wall\b',  # Specific Berlin attractions
                        r'\bMuseum\s+Island\b',  # Specific Berlin attractions
                        r'\bCheckpoint\s+Charlie\b',  # Specific Berlin attractions
                    ]
                    
                    found_attractions = []
                    for pattern in attraction_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:  # Don't limit here, deduplicate later
                            cleaned_match = match.strip()
                            # Filter out HTML fragments, URLs, and other unwanted content
                            if (len(cleaned_match) >= 5 and 
                                not any(char in cleaned_match for char in ['<', '>', '{', '}', '[', ']']) and
                                not cleaned_match.startswith(('http', 'www', 'com', 'TO ', 'TYPE', 'TIME', 'SPEND')) and
                                not cleaned_match.endswith(('...', '–', '-')) and
                                not cleaned_match.upper() in ['TO SPEND', 'TIME TO SPEND', 'TYPE', 'SIGHTSEEING'] and
                                ' ' in cleaned_match):  # Ensure it's not just one word
                                found_attractions.append(cleaned_match)
                    
                    # Deduplicate attractions
                    unique_attraction_names = deduplicate_items(found_attractions, min_items=5)
                    
                    # Convert to the format expected by the UI
                    found_attractions = [{"name": name, "description": "Popular attraction in the destination"} for name in unique_attraction_names]
                    
                    if found_attractions:
                        # Display attractions in columns
                        col1, col2 = st.columns(2)
                        
                        for i, attraction in enumerate(found_attractions[:10]):  # Top 10 attractions
                            with col1 if i % 2 == 0 else col2:
                                st.markdown(f"""
                                <div class="attraction-card">
                                    <h4>{i+1}. {attraction['name']}</h4>
                                    <p>{attraction['description']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Add note if fewer than 5 unique attractions found
                        if len(found_attractions) < 5:
                            st.info(f"ℹ️ Only {len(found_attractions)} unique attractions found for this destination.")
                        
                        attractions_found = True
                        break
    
    if not attractions_found:
        # Fallback: Show message about researched attractions
        st.markdown("""
        <div class="attraction-card">
            <h4>🔍 Destination Research Complete</h4>
            <p>Attractions and activities have been researched for your destination. 
            Check the Summary tab for detailed attraction information extracted from travel guides.</p>
        </div>
        """, unsafe_allow_html=True)

def display_weather(planner_results):
    """Display weather forecast"""
    st.markdown("""
    <div class="section-header">
        <h2>🌤️ Weather Forecast</h2>
    </div>
    """, unsafe_allow_html=True)
    
    weather = planner_results.get("weather_forecast", {})
    if weather and isinstance(weather, dict):
        forecasts = weather.get("forecasts", [])
        
        if forecasts:
            cols = st.columns(min(len(forecasts), 5))  # Max 5 columns
            
            for i, forecast in enumerate(forecasts[:5]):
                with cols[i]:
                    if isinstance(forecast, dict):
                        date = forecast.get("date", "N/A")
                        condition = forecast.get("condition", "N/A")
                        temp_high = forecast.get("temp_high", "N/A")
                        temp_low = forecast.get("temp_low", "N/A")
                        
                        st.markdown(f"""
                        <div class="weather-card">
                            <h5>{date}</h5>
                            <p><strong>{condition}</strong></p>
                            <p>🌡️ {temp_high}° / {temp_low}°</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Display summary
        summary = weather.get("human_readable_summary", "")
        if summary:
            st.markdown(f"""
            <div class="card">
                <h4>📊 Weather Summary</h4>
                <p>{summary}</p>
            </div>
            """, unsafe_allow_html=True)

def display_events(planner_results):
    """Display local events"""
    st.markdown("""
    <div class="section-header">
        <h2>🎉 Local Events</h2>
    </div>
    """, unsafe_allow_html=True)
    
    events = planner_results.get("local_events", [])
    if events and isinstance(events, list):
        with st.expander("View All Events", expanded=True):
            for i, event in enumerate(events[:10]):  # Show top 10 events
                if isinstance(event, dict):
                    title = event.get('title', 'N/A')
                    venue = event.get('venue', 'N/A')
                    date = event.get('formatted_date', 'N/A')
                    description = event.get('description', '')
                    
                    st.markdown(f"""
                    <div class="event-card">
                        <h4>{i+1}. {title}</h4>
                        <p><strong>📍 Venue:</strong> {venue}</p>
                        <p><strong>📅 Date:</strong> {date}</p>
                        {f'<p><strong>📝 Details:</strong> {description[:200]}...</p>' if description else ''}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No local events found for your travel dates.")

def display_cost_summary(calculator_results):
    """Display cost breakdown"""
    st.markdown("""
    <div class="section-header">
        <h2>💰 Cost Summary</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if calculator_results:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h4>✈️ Flights</h4>
                <h3>${calculator_results.get('flight_total', 0):.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>🏨 Hotels</h4>
                <h3>${calculator_results.get('hotel_total', 0):.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h4>🍽️ Daily Expenses</h4>
                <h3>${calculator_results.get('daily_cost_estimate', 120):.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h4>💳 Total Cost</h4>
                <h3>${calculator_results.get('final_quotation', 0):.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed breakdown
        st.markdown(f"""
        <div class="card">
            <h4>📊 Detailed Breakdown</h4>
            <p><strong>Trip Duration:</strong> {calculator_results.get('days', 5)} days</p>
            <p><strong>Subtotal:</strong> ${calculator_results.get('subtotal', 0):.2f}</p>
            <p><strong>Commission ({calculator_results.get('commission_rate', 0.1)*100:.1f}%):</strong> ${calculator_results.get('commission_amount', 0):.2f}</p>
            <p><strong>Final Total:</strong> <span style="font-size: 1.2em; color: #667eea;">${calculator_results.get('final_quotation', 0):.2f}</span></p>
        </div>
        """, unsafe_allow_html=True)

def display_final_summary(final_state):
    """Display the comprehensive final vacation plan"""
    st.markdown("""
    <div class="section-header">
        <h2>📋 Your Complete Vacation Plan</h2>
    </div>
    """, unsafe_allow_html=True)
    
    final_plan = final_state.get("final_plan", "")
    if final_plan and len(final_plan) > 100:
        st.markdown(f"""
        <div class="summary-card">
            <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 8px;">
                {final_plan.replace('# 🌍', '## 🌍').replace('\n', '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="summary-card">
            <h3>🎉 Your Vacation Plan is Ready!</h3>
            <p>All the details above have been compiled into your personalized vacation plan. 
            Use the download button below to get your complete itinerary in Markdown format.</p>
        </div>
        """, unsafe_allow_html=True)

def create_demo_data():
    """Create demo data for testing the UI"""
    return {
        "research_results": {
            "flights": [
                {
                    "airline": "Air France",
                    "flightNumber": "AF1148",
                    "departureAirport": "BCN",
                    "arrivalAirport": "CDG",
                    "departureTime": "08:30",
                    "arrivalTime": "10:15",
                    "durationOutbound": "1h 45m",
                    "priceUSD": 189.50
                },
                {
                    "airline": "Vueling",
                    "flightNumber": "VY8004",
                    "departureAirport": "BCN", 
                    "arrivalAirport": "ORY",
                    "departureTime": "14:20",
                    "arrivalTime": "16:10",
                    "durationOutbound": "1h 50m",
                    "priceUSD": 145.00
                }
            ],
            "accommodations": {
                "hotels": [
                    {
                        "name": "Hotel des Grands Boulevards",
                        "price": {"per_night": "$180"},
                        "rating": 4.2,
                        "address": {"area": "2nd Arrondissement, Central Paris"},
                        "amenities": "WiFi, Restaurant, Bar"
                    },
                    {
                        "name": "Le Marais Hotel",
                        "price": {"per_night": "$145"},
                        "rating": 4.0,
                        "address": {"area": "Le Marais District"},
                        "amenities": "WiFi, Breakfast, Historic Building"
                    }
                ]
            }
        },
        "planner_results": {
            "weather_forecast": {
                "forecasts": [
                    {"date": "Day 1", "condition": "Sunny", "temp_high": 22, "temp_low": 15},
                    {"date": "Day 2", "condition": "Partly Cloudy", "temp_high": 20, "temp_low": 14},
                    {"date": "Day 3", "condition": "Light Rain", "temp_high": 18, "temp_low": 12},
                    {"date": "Day 4", "condition": "Sunny", "temp_high": 24, "temp_low": 16},
                    {"date": "Day 5", "condition": "Clear", "temp_high": 25, "temp_low": 17}
                ],
                "human_readable_summary": "Expect mostly pleasant weather with temperatures ranging from 12-25°C. Pack a light jacket and umbrella for Day 3."
            },
            "local_events": [
                {
                    "title": "Louvre Night Opening",
                    "venue": "Louvre Museum",
                    "formatted_date": "Friday Evening",
                    "description": "Extended hours until 9:45 PM for evening museum visits"
                },
                {
                    "title": "Seine River Jazz Festival",
                    "venue": "Pont Neuf",
                    "formatted_date": "Weekend",
                    "description": "Live jazz performances along the Seine riverbank"
                }
            ]
        },
        "calculator_results": {
            "flight_total": 379.00,
            "hotel_total": 720.00,
            "daily_cost_estimate": 120.00,
            "days": 5,
            "subtotal": 1699.00,
            "commission_rate": 0.1,
            "commission_amount": 169.90,
            "final_quotation": 1868.90
        },
        "final_plan": """# 🌍 Final Vacation Plan: Paris

**Travel Dates:** 5 days in Paris

## ✈️ Recommended Flights
Air France AF1148 - BCN to CDG at 08:30, arriving 10:15 ($189.50)

## 🏨 Recommended Hotels  
Hotel des Grands Boulevards - Central location, $180/night, excellent amenities

## 🎉 Key Events
- Louvre Night Opening (Friday Evening)
- Seine River Jazz Festival (Weekend)

## 🌍 Must-See Attractions
Top 5 attractions: Eiffel Tower, Louvre Museum, Notre-Dame, Arc de Triomphe, Champs-Élysées

## 🌤️ Weather Outlook
Pleasant weather expected, 12-25°C range, light rain on Day 3

## 💰 Cost Summary
Total estimated cost: $1,868.90 for 5 days

## ✅ Summary Recommendation
Perfect 5-day Paris getaway with excellent flight connections, central accommodation, and diverse cultural activities. Budget-friendly options with premium experiences."""
    }

def create_markdown_export(final_state, departure_city, destination_city, start_date, end_date):
    """Create markdown content for export"""
    # Use the existing Markdown export functionality from VacayMate system
    vacay_mate = VacayMate()
    markdown_content = vacay_mate._build_markdown_content(final_state, destination_city, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    return markdown_content

def is_valid_city_local(city_name: str) -> bool:
    """Local city validation function to avoid import issues."""
    if not city_name or not isinstance(city_name, str):
        return False
    
    # Clean and normalize the input
    clean_name = city_name.lower().strip()
    
    # Check if empty after stripping
    if not clean_name:
        return False
    
    # List of supported cities (major cities from around the world)
    supported_cities = [
        # Europe
        'vienna', 'brussels', 'sofia', 'zagreb', 'prague', 'copenhagen', 'helsinki',
        'paris', 'lyon', 'nice', 'berlin', 'munich', 'frankfurt', 'london', 'manchester',
        'athens', 'budapest', 'dublin', 'reykjavik', 'rome', 'milan', 'vilnius',
        'luxembourg', 'valletta', 'amsterdam', 'warsaw', 'lisbon', 'bucharest', 'moscow',
        'saint-petersburg', 'belgrade', 'bratislava', 'ljubljana', 'madrid', 'barcelona',
        'stockholm', 'bern', 'zurich', 'geneva', 'ankara', 'istanbul', 'kyiv',
        
        # North America  
        'toronto', 'vancouver', 'montreal', 'calgary', 'ottawa', 'havana', 'san-jose',
        'guatemala-city', 'port-au-prince', 'kingston', 'mexico-city', 'cancun',
        'guadalajara', 'monterrey', 'panama-city', 'san-salvador', 'new-york', 'newyork',
        'new york', 'los-angeles', 'losangeles', 'los angeles', 'chicago', 'miami',
        'dallas', 'atlanta', 'san-francisco', 'sanfrancisco', 'san francisco', 'denver',
        'boston', 'seattle', 'houston', 'las-vegas', 'lasvegas', 'las vegas',
        'washington-dc', 'washingtondc', 'washington dc', 'honolulu',
        
        # South America
        'buenos-aires', 'buenosaires', 'buenos aires', 'la-paz', 'lapaz', 'la paz',
        'rio-de-janeiro', 'riodejaneiro', 'rio de janeiro', 'sao-paulo', 'saopaulo',
        'sao paulo', 'são paulo', 'brasilia', 'santiago', 'bogota', 'quito',
        'asuncion', 'lima', 'montevideo', 'caracas',
        
        # Middle East & Africa
        'dubai', 'abu-dhabi', 'abudhabi', 'abu dhabi', 'manama', 'cairo', 'addis-ababa',
        'addisababa', 'addis ababa', 'tel-aviv', 'telaviv', 'tel aviv', 'amman',
        'nairobi', 'kuwait', 'beirut', 'casablanca', 'lagos', 'doha', 'riyadh',
        'jeddah', 'dakar', 'johannesburg', 'cape-town', 'capetown', 'cape town',
        
        # Asia & Oceania
        'dhaka', 'beijing', 'shanghai', 'hong-kong', 'hongkong', 'hong kong',
        'jakarta', 'delhi', 'mumbai', 'bengaluru', 'tokyo', 'osaka', 'seoul',
        'colombo', 'kuala-lumpur', 'kualalumpur', 'kuala lumpur', 'kathmandu',
        'manila', 'karachi', 'lahore', 'singapore', 'taipei', 'bangkok',
        'hanoi', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
        'canberra', 'auckland', 'wellington', 'christchurch', 'port-moresby',
        'portmoresby', 'port moresby', 'suva'
    ]
    
    # Check exact match
    if clean_name in supported_cities:
        return True
    
    # Check partial matches
    for city in supported_cities:
        if clean_name in city or city in clean_name:
            return True
    
    return False

def get_city_validation_error_local(city_name: str, field_name: str = "City") -> str:
    """Local city validation error function."""
    if not city_name or not city_name.strip():
        return f"{field_name} is required. Please enter a valid city name."
    
    error_msg = f"'{city_name}' is not a valid city in our database. Please check the spelling and try again."
    error_msg += "\n\nSupported cities include major destinations in Europe, North America, South America, Asia, Africa, and Oceania."
    
    return error_msg

def main():
    
    # Display header
    display_header()
    
    # Input form
    departure_city, destination_city, start_date, end_date = display_input_form()
    
    # Generate button and demo mode
    col1, col2 = st.columns(2)
    
    with col1:
        generate_clicked = st.button("🚀 Generate My Vacation Plan", type="primary")
    
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
                **VacayMate supports major cities from around the world including:**
                
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
            st.stop()  # Use st.stop() instead of return to ensure processing stops
        
        # Show loading spinner
        with st.spinner("🤖 AI is planning your perfect vacation... This may take 30-60 seconds."):
            final_state = run_vacaymate_system(departure_city, destination_city, start_date, end_date)
        
        if final_state:
            st.success("🎉 Your vacation plan is ready!")
            
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
        st.info("🎭 Showing demo results for Barcelona → Paris")
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
            if st.button("📄 Download Complete Plan (Markdown)", type="secondary"):
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
                    filename = f"vacation_plan_{trip_details['destination_city'].lower()}_{timestamp}.md"
                    
                    st.download_button(
                        label="💾 Download Markdown File",
                        data=markdown_content,
                        file_name=filename,
                        mime="text/markdown",
                        type="primary"
                    )
                    
                    st.success(f"📋 Your vacation plan is ready for download as {filename}")
                    
                except Exception as e:
                    st.error(f"Error creating markdown export: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>🌍 <strong>VacayMate</strong> - Your AI-Powered Travel Companion</p>
        <p>Made with ❤️ using Streamlit and advanced AI technology</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
