from langchain.agents import tool
import requests
import os
from dotenv import load_dotenv
#from code.tools.city_mapping import CITY_CODES
load_dotenv()
FLIGHTS_RAPID_API_KEY = os.getenv("FLIGHTS_RAPID_API_KEY")
if not FLIGHTS_RAPID_API_KEY:
    raise ValueError("FLIGHTS_RAPID_API_KEY environment variable not set.")
# City mapping for flight API requests
# This ensures correct city format for the Kiwi API

CITY_CODES = [
    # Europe
    'City:vienna_at',
    'City:brussels_be',
    'City:sofia_bg',
    'City:zagreb_hr',
    'City:prague_cz',
    'City:copenhagen_dk',
    'City:helsinki_fi',
    'City:paris_fr',
    'City:lyon_fr',
    'City:nice_fr',
    'City:berlin_de',
    'City:munich_de',
    'City:frankfurt_de',
    'City:london_gb',
    'City:manchester_gb',
    'City:athens_gr',
    'City:budapest_hu',
    'City:dublin_ie',
    'City:reykjavik_is',
    'City:rome_it',
    'City:milan_it',
    'City:vilnius_lt',
    'City:luxembourg_lu',
    'City:valletta_mt',
    'City:amsterdam_nl',
    'City:warsaw_pl',
    'City:lisbon_pt',
    'City:bucharest_ro',
    'City:moscow_ru',
    'City:saint-petersburg_ru',
    'City:belgrade_rs',
    'City:bratislava_sk',
    'City:ljubljana_si',
    'City:madrid_es',
    'City:barcelona_es',
    'City:stockholm_se',
    'City:bern_ch',
    'City:zurich_ch',
    'City:geneva_ch',
    'City:ankara_tr',
    'City:istanbul_tr',
    'City:kyiv_ua',

    # North America
    'City:toronto_ca',
    'City:vancouver_ca',
    'City:montreal_ca',
    'City:calgary_ca',
    'City:ottawa_ca',
    'City:havana_cu',
    'City:san-jose_cr',
    'City:guatemala-city_gt',
    'City:port-au-prince_ht',
    'City:kingston_jm',
    'City:mexico-city_mx',
    'City:cancun_mx',
    'City:guadalajara_mx',
    'City:monterrey_mx',
    'City:panama-city_pa',
    'City:san-salvador_sv',
    'City:new-york_us',
    'City:los-angeles_us',
    'City:chicago_us',
    'City:miami_us',
    'City:dallas_us',
    'City:atlanta_us',
    'City:san-francisco_us',
    'City:denver_us',
    'City:boston_us',
    'City:seattle_us',
    'City:houston_us',
    'City:las-vegas_us',
    'City:washington-dc_us',
    'City:honolulu_us',

    # South America
    'City:buenos-aires_ar',
    'City:la-paz_bo',
    'City:rio-de-janeiro_br',
    'City:sao-paulo_br',
    'City:brasilia_br',
    'City:santiago_cl',
    'City:bogota_co',
    'City:quito_ec',
    'City:asuncion_py',
    'City:lima_pe',
    'City:montevideo_uy',
    'City:caracas_ve',

    # Middle East & Africa
    'City:dubai_ae',
    'City:abu-dhabi_ae',
    'City:manama_bh',
    'City:cairo_eg',
    'City:addis-ababa_et',
    'City:tel-aviv_il',
    'City:amman_jo',
    'City:nairobi_ke',
    'City:kuwait_kw',
    'City:beirut_lb',
    'City:casablanca_ma',
    'City:lagos_ng',
    'City:doha_qa',
    'City:riyadh_sa',
    'City:jeddah_sa',
    'City:dakar_sn',
    'City:johannesburg_za',
    'City:cape-town_za',
    
    # Asia & Oceania
    'City:dhaka_bd',
    'City:beijing_cn',
    'City:shanghai_cn',
    'City:hong-kong_hk',
    'City:jakarta_id',
    'City:delhi_in',
    'City:mumbai_in',
    'City:bengaluru_in',
    'City:tokyo_jp',
    'City:osaka_jp',
    'City:seoul_kr',
    'City:colombo_lk',
    'City:kuala-lumpur_my',
    'City:kathmandu_np',
    'City:manila_ph',
    'City:karachi_pk',
    'City:lahore_pk',
    'City:singapore_sg',
    'City:taipei_tw',
    'City:bangkok_th',
    'City:hanoi_vn',
    'City:sydney_au',
    'City:melbourne_au',
    'City:brisbane_au',
    'City:perth_au',
    'City:adelaide_au',
    'City:canberra_au',
    'City:auckland_nz',
    'City:wellington_nz',
    'City:christchurch_nz',
    'City:port-moresby_pg',
    'City:suva_fj',
]

def create_city_mapping():
    """Create a mapping from city names to API codes."""
    mapping = {}
    
    for code in CITY_CODES:
        # Extract city name from code (remove 'City:' and country suffix)
        city_part = code.replace('City:', '').split('_')[0]
        
        # Create variations of the city name for matching
        variations = [
            city_part,  # e.g., 'new-york'
            city_part.replace('-', ' '),  # e.g., 'new york'
            city_part.replace('-', ''),   # e.g., 'newyork'
        ]
        
        for variation in variations:
            mapping[variation.lower()] = code
    
    return mapping

# Create the mapping
CITY_MAPPING = create_city_mapping()

def get_city_code(city_name: str) -> str:
    """
    Get the correct API city code for a given city name.
    
    Args:
        city_name: The city name (e.g., 'Barcelona', 'New York', 'amsterdam')
        
    Returns:
        str: The correct API code (e.g., 'City:barcelona_es') or formatted fallback
    """
    if not city_name:
        return ""
    
    # Clean and normalize the input
    clean_name = city_name.lower().strip()
    
    # Try exact match first
    if clean_name in CITY_MAPPING:
        return CITY_MAPPING[clean_name]
    
    # Try partial matches
    for key, value in CITY_MAPPING.items():
        if clean_name in key or key in clean_name:
            return value
    
    # Fallback: create a generic format
    # This maintains the API structure even for unknown cities
    formatted_name = clean_name.replace(' ', '-').replace('_', '-')
    return f"City:{formatted_name}_xx"  # xx as unknown country code

def validate_city_code(code: str) -> bool:
    """Check if a city code is in the valid format."""
    return code.startswith('City:') and '_' in code

def minutes_to_hm(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def simplify_itineraries(raw_response):
    simplified = {"itineraries": []}
    for itin in raw_response.get("itineraries", []):
        # Get duration from the actual segments, not the top level
        outbound_segments = itin.get("outbound", {}).get("sectorSegments", [])
        inbound_segments = itin.get("inbound", {}).get("sectorSegments", [])
        
        # Calculate total duration for outbound - use actual flight duration from API
        duration_outbound_minutes = itin.get("outbound", {}).get("duration", 0)
        
        # Check if duration might be in seconds instead of minutes
        if duration_outbound_minutes > 1440:  # More than 24 hours suggests it's in seconds
            duration_outbound_minutes = duration_outbound_minutes // 60
        
        if duration_outbound_minutes == 0 and outbound_segments:
            # Fallback: sum segment durations
            for segment in outbound_segments:
                segment_duration = segment.get("segment", {}).get("duration", 0)
                # Check if segment duration is in seconds
                if segment_duration > 1440:
                    segment_duration = segment_duration // 60
                duration_outbound_minutes += segment_duration
        
        # Calculate total duration for inbound - use actual flight duration from API
        duration_inbound_minutes = itin.get("inbound", {}).get("duration", 0)
        
        # Check if duration might be in seconds instead of minutes
        if duration_inbound_minutes > 1440:  # More than 24 hours suggests it's in seconds
            duration_inbound_minutes = duration_inbound_minutes // 60
        
        if duration_inbound_minutes == 0 and inbound_segments:
            # Fallback: sum segment durations
            for segment in inbound_segments:
                segment_duration = segment.get("segment", {}).get("duration", 0)
                # Check if segment duration is in seconds
                if segment_duration > 1440:
                    segment_duration = segment_duration // 60
                duration_inbound_minutes += segment_duration

        simplified_itin = {
            "id": itin.get("id"),
            "priceUSD": float(itin.get("price", {}).get("amount", 0)),
            "priceEUR": float(itin.get("priceEur", {}).get("amount", 0)),
            "durationOutbound": minutes_to_hm(duration_outbound_minutes),
            "durationInbound": minutes_to_hm(duration_inbound_minutes),
            "lastAvailableSeats": itin.get("lastAvailable", {}).get("seatsLeft", 0),
            "outbound": {},
            "inbound": {},
            "bookingUrl": None,
            "human_readable_summary": None,
            # Add fields for rich Markdown display
            "airline": None,
            "flightNumber": None,
            "departureAirport": None,
            "arrivalAirport": None,
            "departureTime": None,
            "arrivalTime": None
        }

        # Outbound flight details
        outbound = itin.get("outbound", {}).get("sectorSegments", [])
        if outbound:
            seg = outbound[0].get("segment", {})
            carrier_name = seg.get("carrier", {}).get("name", "Unknown Airline")
            carrier_code = seg.get("carrier", {}).get("code", "XX")
            flight_number = f"{carrier_code}{seg.get('flightNumber', '0000')}"
            
            simplified_itin["outbound"] = {
                "source": seg.get("source", {}).get("station", {}).get("name"),
                "sourceCode": seg.get("source", {}).get("station", {}).get("code"),
                "destination": seg.get("destination", {}).get("station", {}).get("name"),
                "destinationCode": seg.get("destination", {}).get("station", {}).get("code"),
                "departureLocalTime": seg.get("source", {}).get("localTime"),
                "arrivalLocalTime": seg.get("destination", {}).get("localTime"),
                "carrier": carrier_name,
                "carrierCode": carrier_code,
                "flightNumber": flight_number,
                "cabinClass": seg.get("cabinClass"),
                "summary": f"{carrier_name} flight from "
                           f"{seg.get('source', {}).get('station', {}).get('name')} to "
                           f"{seg.get('destination', {}).get('station', {}).get('name')}, departing at "
                           f"{seg.get('source', {}).get('localTime')} and arriving at "
                           f"{seg.get('destination', {}).get('localTime')}"
            }
            
            # Set main flight info for table display (use outbound as primary)
            simplified_itin["airline"] = carrier_name
            simplified_itin["flightNumber"] = flight_number
            simplified_itin["departureAirport"] = f"{seg.get('source', {}).get('station', {}).get('name')} ({seg.get('source', {}).get('station', {}).get('code')})"
            simplified_itin["arrivalAirport"] = f"{seg.get('destination', {}).get('station', {}).get('name')} ({seg.get('destination', {}).get('station', {}).get('code')})"
            simplified_itin["departureTime"] = seg.get("source", {}).get("localTime")
            simplified_itin["arrivalTime"] = seg.get("destination", {}).get("localTime")

        # Inbound flight details
        inbound = itin.get("inbound", {}).get("sectorSegments", [])
        if inbound:
            seg = inbound[0].get("segment", {})
            carrier_name = seg.get("carrier", {}).get("name", "Unknown Airline")
            carrier_code = seg.get("carrier", {}).get("code", "XX")
            flight_number = f"{carrier_code}{seg.get('flightNumber', '0000')}"
            
            simplified_itin["inbound"] = {
                "source": seg.get("source", {}).get("station", {}).get("name"),
                "sourceCode": seg.get("source", {}).get("station", {}).get("code"),
                "destination": seg.get("destination", {}).get("station", {}).get("name"),
                "destinationCode": seg.get("destination", {}).get("station", {}).get("code"),
                "departureLocalTime": seg.get("source", {}).get("localTime"),
                "arrivalLocalTime": seg.get("destination", {}).get("localTime"),
                "carrier": carrier_name,
                "carrierCode": carrier_code,
                "flightNumber": flight_number,
                "cabinClass": seg.get("cabinClass"),
                "summary": f"{carrier_name} flight from "
                           f"{seg.get('source', {}).get('station', {}).get('name')} to "
                           f"{seg.get('destination', {}).get('station', {}).get('name')}, departing at "
                           f"{seg.get('source', {}).get('localTime')} and arriving at "
                           f"{seg.get('destination', {}).get('localTime')}"
            }

        # Booking URL
        booking_edges = itin.get("bookingOptions", {}).get("edges", [])
        if booking_edges:
            simplified_itin["bookingUrl"] = "https://www.kiwi.com" + booking_edges[0].get("node", {}).get("bookingUrl", "")


        # Human-readable summary
        outbound_summary = simplified_itin["outbound"].get("summary")
        inbound_summary = simplified_itin["inbound"].get("summary")
        price = simplified_itin["priceUSD"]
        seats = simplified_itin["lastAvailableSeats"]

        if outbound_summary and inbound_summary:
            simplified_itin["human_readable_summary"] = (
                f"The round-trip flight costs ${price:.2f}. "
                f"The outbound flight is: {outbound_summary}. "
                f"The inbound flight is: {inbound_summary}. "
                f"There are {seats} seats left."
            )
        elif outbound_summary:
            simplified_itin["human_readable_summary"] = (
                f"The one-way flight costs ${price:.2f}. "
                f"The flight is: {outbound_summary}. "
                f"There are {seats} seats left."
            )
        else:
            simplified_itin["human_readable_summary"] = f"A flight option costs ${price:.2f}, but detailed flight information is not available."

        simplified["itineraries"].append(simplified_itin)

    return simplified


# --- LangChain Tool with required dates ---
@tool
def get_flight_prices(
    source: str,
    destination: str,
    adults: int,
    currency: str,
    outboundDepartureDateStart: str,
    outboundDepartureDateEnd: str,
    inboundDepartureDateStart: str,
    inboundDepartureDateEnd: str
):
    """
    Fetches round-trip flight itineraries from the Kiwi API.
    
    Dates are normalized automatically to full ISO format.
    """
    import re
    import requests

    # --- Normalize dates to full ISO ---
    def normalize_date(date_str: str, is_start=True) -> str:
        """Convert YYYY-MM-DD to full ISO datetime."""
        if "T" in date_str:  # already full ISO
            return date_str
        return f"{date_str}T00:00:00" if is_start else f"{date_str}T23:59:59"

    outboundDepartureDateStart = normalize_date(outboundDepartureDateStart, True)
    print(outboundDepartureDateStart)
    outboundDepartureDateEnd = normalize_date(outboundDepartureDateEnd, False)
    print(outboundDepartureDateEnd)
    inboundDepartureDateStart = normalize_date(inboundDepartureDateStart, True)
    print(inboundDepartureDateStart)
    inboundDepartureDateEnd = normalize_date(inboundDepartureDateEnd, False)
    print(inboundDepartureDateEnd)

    # --- helper to normalize city codes ---
    def format_city_code(city_str):
        if isinstance(city_str, str) and city_str.startswith('City:'):
            return city_str
        city_str = str(city_str).strip().lower()
        for code in CITY_CODES:
            if city_str in code.lower():
                return code
        parts = re.split(r'[,_-]', city_str)
        if len(parts) >= 2:
            return f'City:{parts[0]}_{parts[-1][:2]}'
        return f'City:{city_str}'

    # Format source & destination
    source = format_city_code(source)
    destination = format_city_code(destination)

    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip"
    querystring = {
        "source": source,
        "destination": destination,
        "currency": currency.lower(),
        "locale": "en",
        "adults": str(adults),
        "children": "0",
        "infants": "0",
        "handbags": "1",
        "holdbags": "0",
        "cabinClass": "ECONOMY",
        "sortBy": "QUALITY",
        "sortOrder": "ASCENDING",
        "applyMixedClasses": "true",
        "allowReturnFromDifferentCity": "true",
        "allowChangeInboundDestination": "true",
        "allowChangeInboundSource": "true",
        "allowDifferentStationConnection": "true",
        "enableSelfTransfer": "true",
        "allowOvernightStopover": "true",
        "enableTrueHiddenCity": "true",
        "enableThrowAwayTicketing": "true",
        "outbound": "SUNDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,MONDAY,TUESDAY",
        "transportTypes": "FLIGHT",
        "contentProviders": "FLIXBUS_DIRECTS,FRESH,KAYAK,KIWI",
        "limit": "10",
        "outboundDepartureDateStart": outboundDepartureDateStart,
        "outboundDepartureDateEnd": outboundDepartureDateEnd,
        "inboundDepartureDateStart": inboundDepartureDateStart,
        "inboundDepartureDateEnd": inboundDepartureDateEnd,
    }
    headers = {
        "x-rapidapi-key": FLIGHTS_RAPID_API_KEY,
        "x-rapidapi-host": "kiwi-com-cheap-flights.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        status_code = response.status_code

        if status_code != 200:
            return {
                "success": False,
                "error": f"API returned status {status_code}",
                "debug": {"status_code": status_code, "text_snippet": response.text[:200]},
            }

        raw_json = response.json()
        simplified = simplify_itineraries(raw_json)

        flights = simplified.get("itineraries", [])
        return {
            "success": True,
            "flights": flights,
            "count": len(flights),
            "debug": {
                "status_code": status_code,
                "source_formatted": source,
                "destination_formatted": destination,
                "raw_response_keys": list(raw_json.keys()) if isinstance(raw_json, dict) else [],
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "debug": {}
        }

# Step 3: Test the tool
if __name__ == "__main__":
    params = {
        "source": "barcelona",
        "destination": "paris",
        "adults": 1,
        "currency": "USD",
        "outboundDepartureDateStart": "2025-09-15",
        "outboundDepartureDateEnd": "2025-09-15",
        "inboundDepartureDateStart": "2025-09-20",
        "inboundDepartureDateEnd": "2025-09-20"
    }

    result = get_flight_prices.invoke(params)

    import json
    print(json.dumps(result, indent=2))
