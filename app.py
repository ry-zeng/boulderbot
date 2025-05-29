# app.py
from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
from bouldering_agent import BoulderDatabase, BoulderingRecommendationAgent, Boulder

app = Flask(__name__)

# Initialize the database and agent
db = BoulderDatabase('boulders.db')
agent = BoulderingRecommendationAgent(db)

# Sample data for testing
def initialize_sample_data():
    """Add sample bouldering data for testing"""
    sample_boulders = [
        Boulder(
            name="The Nose",
            grade="V4",
            location="Joshua Tree National Park, CA",
            latitude=34.0135,
            longitude=-116.1669,
            approach_distance=0.5,
            route_type="boulder",
            holds=["crimps", "slopers"],
            description="Classic overhang with technical crimping sequence. Great introduction to Joshua Tree granite.",
            url="https://www.mountainproject.com/route/105720495/the-nose",
            rating=4.2,
            height=12.0,
            fa="Unknown"
        ),
        Boulder(
            name="Midnight Lightning",
            grade="V8",
            location="Yosemite Valley, CA",
            latitude=37.7749,
            longitude=-119.4194,
            approach_distance=1.2,
            route_type="boulder",
            holds=["slopers", "mantles"],
            description="Iconic sloper problem on Half Dome boulder. A true test piece of Yosemite.",
            url="https://www.mountainproject.com/route/105833381/midnight-lightning",
            rating=4.8,
            height=15.0,
            fa="Ron Kauk, 1978"
        ),
        Boulder(
            name="Buttermilk Traverse",
            grade="V2",
            location="Bishop, CA",
            latitude=37.3719,
            longitude=-118.4064,
            approach_distance=0.3,
            route_type="boulder",
            holds=["jugs", "crimps"],
            description="Long traverse with great holds and movement. Perfect for beginners.",
            url="https://www.mountainproject.com/route/106028067/buttermilk-traverse",
            rating=3.9,
            height=8.0,
            fa="Unknown"
        ),
        Boulder(
            name="Scream",
            grade="V5",
            location="Joshua Tree National Park, CA",
            latitude=34.0142,
            longitude=-116.1672,
            approach_distance=0.8,
            route_type="boulder",
            holds=["crimps", "pinches"],
            description="Powerful moves on small holds. Technical and sustained.",
            url="https://www.mountainproject.com/route/105720498/scream",
            rating=4.1,
            height=14.0,
            fa="Unknown"
        ),
        Boulder(
            name="Hobbit Hole",
            grade="V3",
            location="Tahoe, CA",
            latitude=39.0968,
            longitude=-120.0324,
            approach_distance=1.5,
            route_type="boulder",
            holds=["jugs", "slopers"],
            description="Fun problem with a tricky topout. Great views of Lake Tahoe.",
            url="https://www.mountainproject.com/route/105833382/hobbit-hole",
            rating=4.0,
            height=10.0,
            fa="Unknown"
        ),
        Boulder(
            name="The Mandala",
            grade="V12",
            location="Bishop, CA",
            latitude=37.3722,
            longitude=-118.4061,
            approach_distance=0.7,
            route_type="boulder",
            holds=["crimps", "slopers"],
            description="World-class testpiece. Incredibly technical and powerful.",
            url="https://www.mountainproject.com/route/105833383/the-mandala",
            rating=4.9,
            height=16.0,
            fa="Chris Sharma, 2000"
        )
    ]
    
    # Check if data already exists
    existing = db.get_boulders_near_location(37.0, -119.0, 500)
    if len(existing) < 5:  # Add sample data if not enough exists
        for boulder in sample_boulders:
            db.add_boulder(boulder)

# Initialize sample data on startup
initialize_sample_data()

@app.route('/')
def index():
    """Main page with search interface"""
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """API endpoint for getting route recommendations"""
    try:
        data = request.get_json()
        
        # Extract parameters
        latitude = float(data.get('latitude', 37.7749))  # Default to SF
        longitude = float(data.get('longitude', -122.4194))
        preferred_grades = data.get('grades', [])
        preferred_holds = data.get('holds', [])
        max_approach = float(data.get('max_approach', 2.0))
        search_radius = float(data.get('search_radius', 100.0))
        
        # Get recommendations
        recommendations = agent.recommend_routes(
            user_location=(latitude, longitude),
            preferred_grades=preferred_grades,
            preferred_holds=preferred_holds,
            max_approach_distance=max_approach,
            search_radius=search_radius,
            limit=10
        )
        
        # Get area statistics
        stats = agent.get_area_statistics((latitude, longitude), search_radius)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/add_route', methods=['POST'])
def add_route():
    """API endpoint for adding new routes"""
    try:
        data = request.get_json()
        
        boulder = Boulder(
            name=data['name'],
            grade=data['grade'],
            location=data['location'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            approach_distance=float(data.get('approach_distance', 0)),
            route_type='boulder',
            holds=data.get('holds', []),
            description=data.get('description', ''),
            url=data.get('url', ''),
            rating=float(data.get('rating', 0)),
            height=float(data.get('height', 0)) if data.get('height') else None,
            fa=data.get('fa', '')
        )
        
        db.add_boulder(boulder)
        
        return jsonify({
            'success': True,
            'message': 'Route added successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
