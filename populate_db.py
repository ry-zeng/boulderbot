#!/usr/bin/env python3
import time
import random
from mp_scraper import MountainProjectScraper
from bouldering_agent import BoulderDatabase
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test with just Birthday Boulders area first
TEST_AREAS = [
    {
        'name': 'Birthday Boulders',
        'url': 'https://www.mountainproject.com/area/105870845/birthday-boulders'
    }
]

def main():
    """Populate database with boulder problems from test area"""
    scraper = MountainProjectScraper()
    db = BoulderDatabase('boulders.db')
    
    total_boulders = 0
    
    # Process test area
    for area in TEST_AREAS:
        logger.info(f"\nScraping boulders in {area['name']}...")
        boulders = scraper.get_area_boulders(area['url'])
        
        # Add boulders to database
        area_count = 0
        for mp_data in boulders:
            try:
                boulder = scraper.convert_to_boulder(mp_data)
                db.add_boulder(boulder)
                area_count += 1
                logger.info(f"Added {boulder.name} ({boulder.grade})")
            except Exception as e:
                logger.error(f"Error adding boulder to database: {e}")
                continue
        
        total_boulders += area_count
        logger.info(f"Added {area_count} boulders from {area['name']}")
    
    logger.info(f"\nTotal boulders added: {total_boulders}")

if __name__ == "__main__":
    main() 