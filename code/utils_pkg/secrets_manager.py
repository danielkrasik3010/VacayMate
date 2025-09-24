"""
Secrets manager utility to handle environment variables and Streamlit secrets
Works for both local development (.env files) and Streamlit Cloud deployment
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

def get_secret(key: str, section: str = None) -> str:
    """
    Get a secret value that works for both local development and Streamlit Cloud
    
    Args:
        key: The secret key name
        section: Optional section name for Streamlit Cloud secrets
    
    Returns:
        The secret value
        
    Raises:
        ValueError: If the secret is not found
    """
    # First try to get from environment variables (local development)
    value = os.getenv(key)
    
    if value:
        return value
    
    # Try to get from Streamlit secrets (cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            if section:
                # Try to get from specific section
                if section in st.secrets and key in st.secrets[section]:
                    return st.secrets[section][key]
            
            # Try to get from root level
            if key in st.secrets:
                return st.secrets[key]
                
            # Try common section mappings
            section_mappings = {
                'FLIGHTS_RAPID_API_KEY': 'flights',
                'SERPAPI_API_KEY': 'serpapi', 
                'TAVILY_API_KEY': 'tavily',
                'OPENAI_API_KEY': 'openai',
                'GROQ_API_KEY': 'groq',
                'GROQ_MODEL': 'groq',
                'OWM_API_KEY': 'owm',
                'LANGSMITH_API_KEY': 'langsmith',
                'LANGSMITH_PROJECT': 'langsmith',
                'LANGSMITH_TRACING': 'langsmith',
                'LANGSMITH_ENDPOINT': 'langsmith'
            }
            
            if key in section_mappings:
                section_name = section_mappings[key]
                if section_name in st.secrets and key in st.secrets[section_name]:
                    return st.secrets[section_name][key]
    
    except ImportError:
        # Streamlit not available (local development)
        pass
    except Exception:
        # Streamlit secrets not available or other error
        pass
    
    # If we get here, the secret was not found
    raise ValueError(f"{key} environment variable or secret not set.")

def get_secret_optional(key: str, section: str = None, default: str = None) -> str:
    """
    Get a secret value with optional default
    
    Args:
        key: The secret key name
        section: Optional section name for Streamlit Cloud secrets
        default: Default value if secret is not found
    
    Returns:
        The secret value or default
    """
    try:
        return get_secret(key, section)
    except ValueError:
        return default
