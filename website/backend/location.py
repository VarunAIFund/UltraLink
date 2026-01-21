"""
Location expansion module - Handles geographic region expansion for search queries
"""
import os
import re
from typing import List, Optional
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize OpenAI client
try:
    client = OpenAI()
except Exception as e:
    print(f"[LOCATION] Warning: OpenAI client could not be initialized: {e}")
    client = None

# Bay Area cities for location expansion
BAY_AREA_CITIES = [
    "San Francisco", "San Jose", "Oakland", "Palo Alto", "Mountain View",
    "Sunnyvale", "Santa Clara", "Fremont", "Redwood City", "San Mateo",
    "Berkeley", "Cupertino", "Menlo Park", "Hayward", "Walnut Creek",
    "Pleasanton", "Livermore", "Daly City", "South San Francisco",
    "San Ramon", "Milpitas", "Foster City", "Burlingame", "Los Altos",
    "Campbell", "Los Gatos", "Saratoga", "Atherton", "Woodside"
]

class LocationExpansion(BaseModel):
    """Structured output for location expansion"""
    location_found: Optional[str] = None
    nearby_cities: List[str] = []

def expand_location_query(query: str) -> str:
    """
    Expand regional location terms in query to list of specific cities.
    This helps the SQL generator match candidates in any city within the region.
    
    Args:
        query: Natural language search query
        
    Returns:
        Query with location terms expanded to specific cities
    """
    expanded_query = query
    
    # 1. Fast path: Expand "Bay Area" (hardcoded common case)
    if "bay area" in query.lower():
        cities_str = ", ".join(BAY_AREA_CITIES)
        expanded_query = re.sub(
            r'\bbay\s*area\b',
            f"any of these cities: {cities_str}",
            expanded_query,
            flags=re.IGNORECASE
        )
        print(f"[LOCATION] Expanded 'Bay Area' to {len(BAY_AREA_CITIES)} cities")
        return expanded_query
    
    # 2. General path: Use LLM to identify location and expand to 25 mile radius
    if not client:
        return expanded_query

    try:
        # Check if we should even try to expand (simple heuristic to avoid LLM call)
        # If query is very short or doesn't look like it has a location, maybe skip?
        # But "San Jose" is short. So we'll try most queries.
        
        system_prompt = """You are a location search assistant. 
        1. Identify if the search query contains a specific city or location (e.g., "San Jose", "New York", "London").
        2. If a location is found, list the top 20 most populated cities/towns within a 25-mile radius of that location (including the location itself).
        3. Return the exact location string found in the query, and the list of nearby cities.
        4. If no specific geographic location is found, return null for location_found.
        """
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {query}"}
            ],
            response_format=LocationExpansion,
            temperature=0.0
        )
        
        result = completion.choices[0].message.parsed
        
        if result.location_found and result.nearby_cities:
            print(f"[LOCATION] Identified location '{result.location_found}' in query")
            print(f"[LOCATION] Expanded to {len(result.nearby_cities)} nearby cities: {', '.join(result.nearby_cities[:5])}...")
            
            # Replace the found location with the expanded list
            # We use regex to replace case-insensitively
            cities_str = ", ".join(result.nearby_cities)
            
            # Escape the location for regex
            escaped_loc = re.escape(result.location_found)
            
            # Replace the location in the query
            # We use a non-capturing group for the replacement to ensure it replaces the whole phrase
            # Using \b word boundaries
            expanded_query = re.sub(
                f"\\b{escaped_loc}\\b", 
                f"any of these cities: {cities_str}", 
                expanded_query, 
                flags=re.IGNORECASE
            )
            
            # If the regex didn't match (e.g. partial word mismatch or boundaries issue), just append the instruction
            if expanded_query == query:
                expanded_query = f"{query} (in any of these cities: {cities_str})"
                
    except Exception as e:
        # Fail gracefully and return original query
        print(f"[LOCATION] Error in location expansion: {e}")
        return query
        
    return expanded_query
