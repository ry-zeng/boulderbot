import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import time
import random
from typing import List, Dict, Optional, Union
import re
from bouldering_agent import Boulder, BoulderDatabase
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MountainProjectScraper:
    """Scraper for Mountain Project boulder problems"""
    
    BASE_URL = "https://www.mountainproject.com"
    
    def __init__(self):
        # Create a session to maintain cookies
        self.session = requests.Session()
        
        # Use a realistic user agent and headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'
        }
        self.session.headers.update(self.headers)

    def _get_page(self, url: str, retry_count: int = 3) -> Optional[BeautifulSoup]:
        """Get a page with retries and random delays"""
        for attempt in range(retry_count):
            try:
                # Add random delay between requests
                delay = random.uniform(5.0, 10.0)
                logger.info(f"Waiting {delay:.2f} seconds before request...")
                time.sleep(delay)
                
                logger.info(f"Fetching page: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                elif response.status_code == 429:  # Too Many Requests
                    logger.warning("Rate limited, waiting longer...")
                    time.sleep(120)  # Wait two minutes before retrying
                else:
                    logger.warning(f"Got status code {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(30)  # Wait 30 seconds before retrying
                
        return None

    def get_area_boulders(self, area_url: str) -> List[Dict]:
        """Get all boulder problems in an area"""
        boulders = []
        soup = self._get_page(area_url)
        if not soup:
            return boulders

        # Find all route links in the area
        route_links = soup.find_all('a', href=re.compile(r'/route/\d+/'))
        if not route_links:
            logger.warning(f"No route links found at {area_url}")
            return boulders

        for link in route_links:
            try:
                if not isinstance(link, Tag):
                    continue
                    
                href = link.get('href')
                if not href or not isinstance(href, str):
                    continue

                # Make sure it's an absolute URL
                route_url = urljoin(self.BASE_URL, href)

                # Get detailed boulder info
                boulder_data = self._parse_boulder_page(route_url)
                if boulder_data:
                    boulders.append(boulder_data)
                    logger.info(f"Added boulder: {boulder_data['name']}")

            except Exception as e:
                logger.error(f"Error processing link: {str(e)}")
                continue

        return boulders

    def _parse_boulder_page(self, url: str) -> Optional[Dict]:
        """Parse a boulder problem page"""
        soup = self._get_page(url)
        if not soup:
            return None

        try:
            # Get name from the h1 title
            name_elem = soup.find('h1')
            if not name_elem or not isinstance(name_elem, Tag):
                return None
            name = name_elem.text.strip()
            
            # Get grade from the route stats section
            grade = None
            stats_table = soup.find('table', {'class': 'description-details'})
            if stats_table and isinstance(stats_table, Tag):
                for row in stats_table.find_all('tr'):
                    if not isinstance(row, Tag):
                        continue
                    cells = row.find_all('td')
                    if len(cells) >= 2 and 'Grade:' in cells[0].text:
                        grade = cells[1].text.strip()
                        break
            
            if not grade:
                return None
                
            # Only process boulder problems (V grades)
            if not any(x in grade for x in ['V0', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14', 'V15', 'V16']):
                return None
            
            # Get description from the route description section
            description = ""
            desc_section = soup.find('div', {'class': 'fr-view'})
            if desc_section and isinstance(desc_section, Tag):
                description = desc_section.text.strip()
            
            # Get location breadcrumb
            location = []
            breadcrumb = soup.find('div', {'class': 'mb-half'})
            if breadcrumb and isinstance(breadcrumb, Tag):
                for a in breadcrumb.find_all('a'):
                    if isinstance(a, Tag):
                        location.append(a.text.strip())
            
            return {
                'name': name,
                'grade': grade,
                'description': description,
                'location': ' > '.join(location) if location else "",
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error parsing boulder page {url}: {str(e)}")
            return None

    def convert_to_boulder(self, mp_data: Dict) -> Boulder:
        """Convert Mountain Project data to a Boulder object"""
        # Extract V-grade number
        grade_match = re.search(r'V(\d+)', mp_data['grade'])
        v_grade = f"V{grade_match.group(1)}" if grade_match else "VB"
        
        return Boulder(
            name=mp_data['name'],
            grade=v_grade,
            description=mp_data['description'],
            location=mp_data['location'],
            url=mp_data['url'],
            latitude=0.0,  # We'll add these later if needed
            longitude=0.0,
            approach_distance=0.0,
            route_type='boulder',
            holds=[],
            rating=0.0
        )

def main():
    """Example usage of the Mountain Project scraper"""
    scraper = MountainProjectScraper()
    db = BoulderDatabase('boulders.db')
    
    # Example: Scrape Bishop boulders
    area_url = "https://www.mountainproject.com/area/106064825/bishop-area-bouldering"
    print(f"Scraping boulders from {area_url}...")
    
    boulders = scraper.get_area_boulders(area_url)
    print(f"Found {len(boulders)} boulders")
    
    # Add to database
    for mp_data in boulders:
        try:
            boulder = scraper.convert_to_boulder(mp_data)
            db.add_boulder(boulder)
            print(f"Added {boulder.name} ({boulder.grade})")
        except Exception as e:
            print(f"Error adding boulder to database: {e}")
            continue

if __name__ == "__main__":
    main() 