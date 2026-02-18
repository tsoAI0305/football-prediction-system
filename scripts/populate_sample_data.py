"""
Sample data population script for testing the API
"""
import requests
from datetime import datetime, timedelta
import json


BASE_URL = "http://localhost:8000"


def create_teams():
    """Create sample teams"""
    teams = [
        {
            "name": "Manchester City",
            "league": "Premier League",
            "country": "England"
        },
        {
            "name": "Liverpool",
            "league": "Premier League",
            "country": "England"
        },
        {
            "name": "Arsenal",
            "league": "Premier League",
            "country": "England"
        },
        {
            "name": "Tottenham",
            "league": "Premier League",
            "country": "England"
        },
        {
            "name": "Chelsea",
            "league": "Premier League",
            "country": "England"
        }
    ]
    
    team_ids = {}
    
    for team in teams:
        try:
            # Try to create team (may fail if already exists)
            response = requests.post(f"{BASE_URL}/teams/", json=team)
            if response.status_code in [200, 201]:
                team_id = response.json()["id"]
                team_ids[team["name"]] = team_id
                print(f"Created team: {team['name']} (ID: {team_id})")
        except Exception as e:
            print(f"Error creating team {team['name']}: {e}")
    
    return team_ids


def create_matches(team_ids):
    """Create sample matches"""
    if len(team_ids) < 2:
        print("Not enough teams to create matches")
        return []
    
    teams_list = list(team_ids.keys())
    base_date = datetime.now() + timedelta(days=3)
    
    matches = [
        {
            "home_team_id": team_ids[teams_list[0]],
            "away_team_id": team_ids[teams_list[1]],
            "league": "Premier League",
            "season": "2023-24",
            "match_date": (base_date + timedelta(days=0)).isoformat(),
            "home_odds": 2.1,
            "draw_odds": 3.4,
            "away_odds": 3.2
        },
        {
            "home_team_id": team_ids[teams_list[2]],
            "away_team_id": team_ids[teams_list[3]],
            "league": "Premier League",
            "season": "2023-24",
            "match_date": (base_date + timedelta(days=1)).isoformat(),
            "home_odds": 2.3,
            "draw_odds": 3.2,
            "away_odds": 3.0
        },
        {
            "home_team_id": team_ids[teams_list[4]],
            "away_team_id": team_ids[teams_list[0]],
            "league": "Premier League",
            "season": "2023-24",
            "match_date": (base_date + timedelta(days=2)).isoformat(),
            "home_odds": 3.5,
            "draw_odds": 3.3,
            "away_odds": 2.0
        }
    ]
    
    match_ids = []
    
    for match in matches:
        try:
            response = requests.post(f"{BASE_URL}/matches/", json=match)
            if response.status_code in [200, 201]:
                match_id = response.json()["id"]
                match_ids.append(match_id)
                print(f"Created match ID: {match_id}")
        except Exception as e:
            print(f"Error creating match: {e}")
    
    return match_ids


def generate_predictions(match_ids):
    """Generate predictions for matches"""
    for match_id in match_ids:
        try:
            response = requests.post(
                f"{BASE_URL}/predictions/generate/{match_id}",
                params={"include_llm_analysis": False}  # Set to True if you have GROQ_API_KEY
            )
            if response.status_code in [200, 201]:
                prediction = response.json()
                print(f"Generated prediction for match {match_id}:")
                print(f"  Home: {prediction['home_win_probability']*100:.1f}%")
                print(f"  Draw: {prediction['draw_probability']*100:.1f}%")
                print(f"  Away: {prediction['away_win_probability']*100:.1f}%")
        except Exception as e:
            print(f"Error generating prediction for match {match_id}: {e}")


def main():
    """Main function to populate sample data"""
    print("=" * 50)
    print("Football Prediction System - Sample Data Loader")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("API is not running. Please start it first.")
            return
    except Exception as e:
        print(f"Cannot connect to API at {BASE_URL}")
        print("Please make sure the API is running (docker-compose up or uvicorn)")
        return
    
    print("\n1. Creating teams...")
    team_ids = create_teams()
    
    if team_ids:
        print(f"\n2. Creating matches...")
        match_ids = create_matches(team_ids)
        
        if match_ids:
            print(f"\n3. Generating predictions...")
            generate_predictions(match_ids)
    
    print("\n" + "=" * 50)
    print("Sample data loading complete!")
    print("Visit http://localhost:8000/docs to explore the API")
    print("=" * 50)


if __name__ == "__main__":
    main()
