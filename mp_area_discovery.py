#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup, Tag
import time
import random
from typing import List, Dict, Set
from queue import Queue
import json

class AreaDiscovery:
    """Discovers all bouldering areas on Mountain Project"""
    
    BASE_URL = "https://www.mountainproject.com"
    
    def __init__(self):
        # Use a realistic user agent
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.visited_urls = set()
        self.bouldering_areas = []
    
    def discover_areas(self, start_url: str = "https://www.mountainproject.com/route-guide") -> List[Dict]:
        """
        Discover all bouldering areas starting from the main route guide
        Uses breadth-first search to explore the area hierarchy
        """
        queue = Queue()
        queue.put(start_url)
        
        while not queue.empty():
            current_url = queue.get()
            
            if current_url in self.visited_urls:
                continue
                
            try:
                print(f"Exploring {current_url}")
                response = self.session.get(current_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Mark as visited
                self.visited_urls.add(current_url)
                
                # Check if this is a bouldering area
                if self._is_bouldering_area(soup):
                    area_name = self._get_area_name(soup)
                    print(f"Found bouldering area: {area_name}")
                    self.bouldering_areas.append({
                        'name': area_name,
                        'url': current_url
                    })
                
                # Find sub-areas
                sub_areas = self._get_sub_areas(soup)
                for sub_area in sub_areas:
                    if sub_area not in self.visited_urls:
                        queue.put(sub_area)
                
                # Be nice to the server
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Error processing {current_url}: {e}")
                continue
        
        return self.bouldering_areas
    
    def _is_bouldering_area(self, soup: BeautifulSoup) -> bool:
        """Check if the page represents a bouldering area"""
        # Look for indicators that this is a bouldering area
        indicators = [
            'bouldering',
            'boulder problems',
            'boulder area',
            'boulders'
        ]
        
        # Check page title and description
        title = soup.find('h1')
        if title and isinstance(title, Tag):
            title_text = title.text.lower()
            if any(indicator in title_text for indicator in indicators):
                return True
        
        # Check for route table with boulder problems
        route_table = soup.find('table', {'id': 'left-nav-route-table'})
        if route_table and isinstance(route_table, Tag):
            rows = route_table.find_all('tr')
            for row in rows:
                if not isinstance(row, Tag):
                    continue
                route_type = row.find('td', class_='tright')
                if route_type and isinstance(route_type, Tag) and 'Boulder' in route_type.text:
                    return True
        
        return False
    
    def _get_area_name(self, soup: BeautifulSoup) -> str:
        """Extract the area name from the page"""
        title = soup.find('h1')
        return title.text.strip() if title else "Unknown Area"
    
    def _get_sub_areas(self, soup: BeautifulSoup) -> Set[str]:
        """Extract links to sub-areas"""
        sub_areas = set()
        
        # Look for area links in the left-hand navigation
        area_links = soup.find_all('a', href=True)
        for link in area_links:
            href = link['href']
            if '/area/' in href:
                full_url = self.BASE_URL + href if href.startswith('/') else href
                sub_areas.add(full_url)
        
        return sub_areas
    
    def save_areas(self, filename: str = 'bouldering_areas.json'):
        """Save discovered areas to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.bouldering_areas, f, indent=2)
        print(f"Saved {len(self.bouldering_areas)} areas to {filename}")

def main():
    """Discover all bouldering areas on Mountain Project"""
    discoverer = AreaDiscovery()
    
    print("Starting area discovery...")
    areas = discoverer.discover_areas()
    
    print(f"\nFound {len(areas)} bouldering areas!")
    discoverer.save_areas()

if __name__ == "__main__":
    main() 