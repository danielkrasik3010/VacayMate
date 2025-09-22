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

def is_valid_city(city_name: str) -> bool:
    """
    Check if a city name is valid (exists in our mapping).
    
    Args:
        city_name: The city name to validate
        
    Returns:
        bool: True if the city is valid, False otherwise
    """
    if not city_name or not isinstance(city_name, str):
        return False
    
    # Clean and normalize the input
    clean_name = city_name.lower().strip()
    
    # Check if empty after stripping
    if not clean_name:
        return False
    
    # Check exact match
    if clean_name in CITY_MAPPING:
        return True
    
    # Check partial matches
    for key in CITY_MAPPING.keys():
        if clean_name in key or key in clean_name:
            return True
    
    return False

def get_city_validation_error(city_name: str, field_name: str = "City") -> str:
    """
    Get a validation error message for an invalid city.
    
    Args:
        city_name: The invalid city name
        field_name: The field name for the error message
        
    Returns:
        str: Error message with suggestions
    """
    if not city_name or not city_name.strip():
        return f"{field_name} is required. Please enter a valid city name."
    
    # Find close matches
    clean_name = city_name.lower().strip()
    suggestions = []
    
    # Look for cities that start with the same letters
    for key in CITY_MAPPING.keys():
        if key.startswith(clean_name[:3]) and len(clean_name) >= 3:
            # Convert back to display format
            display_name = key.replace('-', ' ').title()
            if display_name not in suggestions:
                suggestions.append(display_name)
        if len(suggestions) >= 3:  # Limit suggestions
            break
    
    error_msg = f"'{city_name}' is not a valid city in our database."
    
    if suggestions:
        error_msg += f" Did you mean: {', '.join(suggestions)}?"
    else:
        error_msg += " Please check the spelling and try again."
    
    error_msg += "\n\nSupported cities include major destinations in Europe, North America, South America, Asia, Africa, and Oceania."
    
    return error_msg

def validate_city_code(code: str) -> bool:
    """Check if a city code is in the valid format."""
    return code.startswith('City:') and '_' in code

# Test function
if __name__ == "__main__":
    test_cities = ['Barcelona', 'Amsterdam', 'New York', 'Warsaw', 'Dubrovnik']
    
    print("Testing city mapping:")
    for city in test_cities:
        code = get_city_code(city)
        print(f"{city} -> {code}")
