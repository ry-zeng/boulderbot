import requests
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import os
from bouldering_agent import Boulder

class MountainProjectAPI:
    """Client for the Mountain Project API"""
    
    BASE_URL = "https://www.mountainproject.com/data"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_area_by_lat_lon(self, lat: float, lon: float, max_distance: float = 50,
                           max_results: int = 500) -> List[Dict]:
        """Get areas within a radius of coordinates"""
        endpoint = f"{self.BASE_URL}/get-routes-for-lat-lon"
        params = {
            'key': self.api_key,
            'lat': lat,
            'lon': lon,
            'maxDistance': max_distance,
            'maxResults': max_results,
            'type': 'boulder'  # Only get boulder problems
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()['routes']
    
    def get_area_by_id(self, area_id: int) -> Dict:
        """Get details for a specific area by ID"""
        endpoint = f"{self.BASE_URL}/get-routes"
        params = {
            'key': self.api_key,
            'routeIds': area_id
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()['routes'][0]

    def convert_to_boulder(self, mp_route: Dict) -> Boulder:
        """Convert Mountain Project route data to our Boulder format"""
        
        # Extract holds from route description
        holds = []
        desc_lower = mp_route.get('description', '').lower()
        possible_holds = ['crimps', 'jugs', 'slopers', 'pinches', 'pockets', 'sidepulls', 'underclings']
        holds = [hold for hold in possible_holds if hold in desc_lower]
        
        # Convert YDS grade to V-scale if needed
        grade = self._normalize_grade(mp_route.get('rating', ''))
        
        return Boulder(
            name=mp_route['name'],
            grade=grade,
            location=mp_route.get('location', [])[-1] if mp_route.get('location') else '',
            latitude=float(mp_route['latitude']),
            longitude=float(mp_route['longitude']),
            approach_distance=0.1,  # MP API doesn't provide approach distance
            route_type='boulder',
            holds=holds,
            description=mp_route.get('description', ''),
            url=mp_route['url'],
            rating=float(mp_route.get('stars', 0)),
            height=float(mp_route.get('height', 0)) if mp_route.get('height') else None,
            fa=mp_route.get('fa', '')
        )
    
    def _normalize_grade(self, grade: str) -> str:
        """Normalize Mountain Project grades to V-scale"""
        # MP already uses V-scale for boulders, but sometimes includes ranges
        # Convert "V1-2" to "V1" etc.
        if '-' in grade:
            grade = grade.split('-')[0]
        return grade.strip()

def fetch_and_store_area_data(api: MountainProjectAPI, db, lat: float, lon: float,
                            radius: float = 50) -> int:
    """
    Fetch boulder problems from an area and store them in the database
    
    Args:
        api: MountainProjectAPI instance
        db: BoulderDatabase instance
        lat: Latitude of center point
        lon: Longitude of center point
        radius: Search radius in miles
        
    Returns:
        Number of boulders added to database
    """
    try:
        # Get all routes in the area
        routes = api.get_area_by_lat_lon(lat, lon, radius)
        
        count = 0
        for route in routes:
            try:
                # Convert to our Boulder format
                boulder = api.convert_to_boulder(route)
                
                # Add to database
                db.add_boulder(boulder)
                count += 1
                
                # Be nice to the API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing route {route.get('id', 'unknown')}: {e}")
                continue
        
        return count
        
    except Exception as e:
        print(f"Error fetching area data: {e}")
        return 0

def main():
    """Example usage of the Mountain Project API client"""
    # Get API key from environment variable
    api_key = os.getenv('MP_API_KEY')
    if not api_key:
        print("Please set the MP_API_KEY environment variable")
        return
    
    # Initialize API client
    api = MountainProjectAPI(api_key)
    
    # Example: Get boulders near Boulder, CO
    try:
        routes = api.get_area_by_lat_lon(40.0150, -105.2705)
        print(f"Found {len(routes)} routes")
        
        # Print first route details
        if routes:
            boulder = api.convert_to_boulder(routes[0])
            print("\nExample boulder:")
            print(f"Name: {boulder.name}")
            print(f"Grade: {boulder.grade}")
            print(f"Location: {boulder.location}")
            print(f"Description: {boulder.description[:100]}...")
            print(f"URL: {boulder.url}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 