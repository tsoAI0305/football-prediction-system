from fastapi.testclient import TestClient
from app.models.team import Team
from app.models.match import Match
from datetime import datetime, timedelta


def test_get_matches_empty(client: TestClient):
    """Test getting matches when none exist"""
    response = client.get("/matches/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_match(client: TestClient, db_session):
    """Test creating a new match"""
    # First create teams
    home_team = Team(
        name="Manchester City",
        league="Premier League",
        country="England",
        wins=15, draws=3, losses=2,
        goals_for=48, goals_against=18,
        points=48
    )
    away_team = Team(
        name="Liverpool",
        league="Premier League",
        country="England",
        wins=14, draws=4, losses=2,
        goals_for=45, goals_against=20,
        points=46
    )
    db_session.add(home_team)
    db_session.add(away_team)
    db_session.commit()
    
    # Create match
    match_data = {
        "home_team_id": home_team.id,
        "away_team_id": away_team.id,
        "league": "Premier League",
        "season": "2023-24",
        "match_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "home_odds": 2.1,
        "draw_odds": 3.4,
        "away_odds": 3.2
    }
    
    response = client.post("/matches/", json=match_data)
    assert response.status_code == 201
    data = response.json()
    assert data["league"] == "Premier League"
    assert data["home_team_id"] == home_team.id
    assert data["away_team_id"] == away_team.id


def test_get_match_by_id(client: TestClient, db_session):
    """Test getting a specific match by ID"""
    # Create teams
    home_team = Team(
        name="Arsenal",
        league="Premier League",
        country="England",
        points=44
    )
    away_team = Team(
        name="Tottenham",
        league="Premier League",
        country="England",
        points=37
    )
    db_session.add(home_team)
    db_session.add(away_team)
    db_session.commit()
    
    # Create match
    match = Match(
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        league="Premier League",
        season="2023-24",
        match_date=datetime.now() + timedelta(days=5)
    )
    db_session.add(match)
    db_session.commit()
    
    # Get match
    response = client.get(f"/matches/{match.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == match.id
    assert data["league"] == "Premier League"


def test_get_nonexistent_match(client: TestClient):
    """Test getting a match that doesn't exist"""
    response = client.get("/matches/9999")
    assert response.status_code == 404


def test_update_match(client: TestClient, db_session):
    """Test updating match results"""
    # Create teams and match
    home_team = Team(name="Chelsea", league="Premier League", country="England")
    away_team = Team(name="Manchester United", league="Premier League", country="England")
    db_session.add(home_team)
    db_session.add(away_team)
    db_session.commit()
    
    match = Match(
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        league="Premier League",
        season="2023-24",
        match_date=datetime.now()
    )
    db_session.add(match)
    db_session.commit()
    
    # Update match with results
    update_data = {
        "home_score": 2,
        "away_score": 1,
        "is_finished": True
    }
    
    response = client.put(f"/matches/{match.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["home_score"] == 2
    assert data["away_score"] == 1
    assert data["is_finished"] is True
