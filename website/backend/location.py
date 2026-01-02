"""
Location expansion module - Handles geographic region expansion for search queries
"""
import re

# Bay Area cities for location expansion
BAY_AREA_CITIES = [
    "San Francisco", "San Jose", "Oakland", "Palo Alto", "Mountain View",
    "Sunnyvale", "Santa Clara", "Fremont", "Redwood City", "San Mateo",
    "Berkeley", "Cupertino", "Menlo Park", "Hayward", "Walnut Creek",
    "Pleasanton", "Livermore", "Daly City", "South San Francisco",
    "San Ramon", "Milpitas", "Foster City", "Burlingame", "Los Altos",
    "Campbell", "Los Gatos", "Saratoga", "Atherton", "Woodside"
]


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
    
    # Expand Bay Area
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

