import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json
import time
from geopy.distance import geodesic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
from datetime import datetime

@dataclass
class Boulder:
    """Data class for boulder route information"""
    name: str
    grade: str
    location: str
    latitude: float
    longitude: float
    approach_distance: float  # in miles
    route_type: str
    holds: List[str]
    description: str
    url: str
    rating: float
    height: Optional[float] = None
    fa: Optional[str] = None  # First ascent
    
class BoulderingScraper:
    """Scraper for Mountain Project and TheCrag"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_mountain_project(self, area_url: str) -> List[Boulder]:
        """Scrape boulder routes from Mountain Project"""
        boulders = []
        
        # Note: Mountain Project has an API - recommend using that instead
        # This is a simplified example of web scraping approach
        try:
            response = self.session.get(area_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse route information (structure varies by page)
            route_elements = soup.find_all('div', class_='route-row')
            
            for route in route_elements:
                try:
                    name = route.find('a', class_='route-name').text.strip()
                    grade = route.find('span', class_='grade').text.strip()
                    
                    # Extract additional details
                    boulder = Boulder(
                        name=name,
                        grade=self._normalize_grade(grade),
                        location="",  # Extract from page context
                        latitude=0.0,  # Would need to extract coordinates
                        longitude=0.0,
                        approach_distance=0.0,
                        route_type="boulder",
                        holds=[],
                        description="",
                        url=area_url,
                        rating=0.0
                    )
                    boulders.append(boulder)
                    
                except Exception as e:
                    print(f"Error parsing route: {e}")
                    
            time.sleep(1)  # Be respectful with requests
            
        except Exception as e:
            print(f"Error scraping {area_url}: {e}")
            
        return boulders
    
    def scrape_thecrag(self, area_url: str) -> List[Boulder]:
        """Scrape boulder routes from TheCrag"""
        # Similar implementation for TheCrag
        # TheCrag also has API access which would be preferred
        pass
    
    def _normalize_grade(self, grade: str) -> str:
        """Normalize different grading systems to V-scale"""
        # Convert Font, British, etc. to V-scale
        grade_map = {
            "4": "V0", "4+": "V0+", "5": "V1", "5+": "V1",
            "6A": "V3", "6A+": "V3", "6B": "V4", "6B+": "V4",
            "6C": "V5", "6C+": "V5", "7A": "V6", "7A+": "V7",
            "7B": "V8", "7B+": "V9", "7C": "V10", "7C+": "V11"
        }
        return grade_map.get(grade.upper(), grade)

class BoulderDatabase:
    """SQLite database for storing boulder route data"""
    
    def __init__(self, db_path: str = "boulders.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boulders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                grade TEXT,
                location TEXT,
                latitude REAL,
                longitude REAL,
                approach_distance REAL,
                route_type TEXT,
                holds TEXT,  -- JSON array of hold types
                description TEXT,
                url TEXT,
                rating REAL,
                height REAL,
                fa TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_location ON boulders(latitude, longitude);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grade ON boulders(grade);
        ''')
        
        conn.commit()
        conn.close()
    
    def add_boulder(self, boulder: Boulder):
        """Add a boulder to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO boulders (name, grade, location, latitude, longitude, 
                                approach_distance, route_type, holds, description, 
                                url, rating, height, fa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            boulder.name, boulder.grade, boulder.location, boulder.latitude,
            boulder.longitude, boulder.approach_distance, boulder.route_type,
            json.dumps(boulder.holds), boulder.description, boulder.url,
            boulder.rating, boulder.height, boulder.fa
        ))
        
        conn.commit()
        conn.close()
    
    def get_boulders_near_location(self, lat: float, lon: float, 
                                 radius_miles: float = 50) -> List[Dict]:
        """Get boulders within radius of a location"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM boulders 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ''')
        
        all_boulders = cursor.fetchall()
        nearby_boulders = []
        
        for boulder in all_boulders:
            boulder_location = (boulder[4], boulder[5])  # lat, lon
            user_location = (lat, lon)
            
            distance = geodesic(user_location, boulder_location).miles
            
            if distance <= radius_miles:
                boulder_dict = {
                    'id': boulder[0], 'name': boulder[1], 'grade': boulder[2],
                    'location': boulder[3], 'latitude': boulder[4], 'longitude': boulder[5],
                    'approach_distance': boulder[6], 'route_type': boulder[7],
                    'holds': json.loads(boulder[8]) if boulder[8] else [],
                    'description': boulder[9], 'url': boulder[10], 'rating': boulder[11],
                    'height': boulder[12], 'fa': boulder[13], 'distance': distance
                }
                nearby_boulders.append(boulder_dict)
        
        conn.close()
        return sorted(nearby_boulders, key=lambda x: x['distance'])

class BoulderingRecommendationAgent:
    """AI agent for recommending bouldering routes"""
    
    def __init__(self, database: BoulderDatabase):
        self.db = database
        self.grade_difficulty = {
            'VB': 0, 'V0-': 1, 'V0': 2, 'V0+': 3, 'V1': 4, 'V2': 5,
            'V3': 6, 'V4': 7, 'V5': 8, 'V6': 9, 'V7': 10, 'V8': 11,
            'V9': 12, 'V10': 13, 'V11': 14, 'V12': 15, 'V13': 16, 'V14': 17
        }
    
    def recommend_routes(self, user_location: Tuple[float, float],
                        preferred_grades: List[str] = None,
                        preferred_holds: List[str] = None,
                        max_approach_distance: float = 2.0,
                        search_radius: float = 50.0,
                        limit: int = 10) -> List[Dict]:
        """
        Recommend bouldering routes based on user preferences
        
        Args:
            user_location: (latitude, longitude)
            preferred_grades: List of grades like ['V3', 'V4', 'V5']
            preferred_holds: List of hold types like ['crimps', 'jugs', 'slopers']
            max_approach_distance: Maximum approach distance in miles
            search_radius: Search radius from user location in miles
            limit: Maximum number of recommendations
        """
        
        # Get nearby boulders
        candidates = self.db.get_boulders_near_location(
            user_location[0], user_location[1], search_radius
        )
        
        # Filter by approach distance
        candidates = [b for b in candidates 
                     if b['approach_distance'] <= max_approach_distance]
        
        # Apply strict grade filtering if preferred grades are specified
        if preferred_grades:
            candidates = [b for b in candidates if b['grade'] in preferred_grades]
        
        # Apply strict hold filtering if preferred holds are specified
        if preferred_holds:
            candidates = [b for b in candidates 
                        if all(hold in b['holds'] for hold in preferred_holds)]
        
        # Score remaining candidates
        scored_routes = []
        for boulder in candidates:
            score = self._calculate_base_score(boulder)
            boulder['recommendation_score'] = score
            scored_routes.append(boulder)
        
        # Sort by score and return top recommendations
        recommendations = sorted(scored_routes, 
                               key=lambda x: x['recommendation_score'], 
                               reverse=True)[:limit]
        
        return recommendations
    
    def _calculate_base_score(self, boulder: Dict) -> float:
        """Calculate base score for a boulder without grade/hold preferences"""
        score = 0.0
        
        # Base score from rating
        score += boulder.get('rating', 0) * 20
        
        # Distance penalty (closer is better)
        distance = boulder.get('distance', 0)
        score -= distance * 0.5
        
        # Approach distance penalty
        approach = boulder.get('approach_distance', 0)
        score -= approach * 2
        
        return score
    
    def get_area_statistics(self, user_location: Tuple[float, float],
                          search_radius: float = 50.0) -> Dict:
        """Get statistics about bouldering in the area"""
        boulders = self.db.get_boulders_near_location(
            user_location[0], user_location[1], search_radius
        )
        
        if not boulders:
            return {"total_routes": 0}
        
        grades = [b['grade'] for b in boulders if b['grade']]
        grade_counts = {}
        for grade in grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        avg_rating = np.mean([b['rating'] for b in boulders if b['rating']])
        
        return {
            "total_routes": len(boulders),
            "grade_distribution": grade_counts,
            "average_rating": round(avg_rating, 2),
            "average_approach": round(np.mean([b['approach_distance'] 
                                            for b in boulders]), 2)
        }

# Example usage
def main():
    """Example usage of the bouldering recommendation agent"""
    
    # Initialize components
    db = BoulderDatabase()
    agent = BoulderingRecommendationAgent(db)
    
    # Example: Add some sample boulders (in practice, scrape from websites)
    sample_boulders = [
        Boulder(
            name="The Nose",
            grade="V4",
            location="Joshua Tree, CA",
            latitude=34.0135,
            longitude=-116.1669,
            approach_distance=0.5,
            route_type="boulder",
            holds=["crimps", "slopers"],
            description="Classic overhang with technical crimping",
            url="https://www.mountainproject.com/route/...",
            rating=4.2
        ),
        Boulder(
            name="Midnight Lightning",
            grade="V8",
            location="Yosemite, CA",
            latitude=37.7749,
            longitude=-119.4194,
            approach_distance=1.2,
            route_type="boulder",
            holds=["slopers", "mantles"],
            description="Iconic sloper problem on Half Dome boulder",
            url="https://www.mountainproject.com/route/...",
            rating=4.8
        )
    ]
    
    # Add sample data
    for boulder in sample_boulders:
        db.add_boulder(boulder)
    
    # Get recommendations for user in California
    user_location = (34.0522, -118.2437)  # Los Angeles
    recommendations = agent.recommend_routes(
        user_location=user_location,
        preferred_grades=['V3', 'V4', 'V5'],
        preferred_holds=['crimps', 'jugs'],
        max_approach_distance=2.0,
        search_radius=100.0
    )
    
    print("Recommended Routes:")
    for i, route in enumerate(recommendations, 1):
        print(f"{i}. {route['name']} ({route['grade']})")
        print(f"   Location: {route['location']}")
        print(f"   Distance: {route['distance']:.1f} miles")
        print(f"   Approach: {route['approach_distance']} miles")
        print(f"   Score: {route['recommendation_score']:.1f}")
        print()
    
    # Get area statistics
    stats = agent.get_area_statistics(user_location, 100.0)
    print("Area Statistics:", stats)

if __name__ == "__main__":
    main()
