"""API endpoint tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.team import Team
from app.models.match import Match, MatchStatus
from app.models.prediction import Prediction, PredictionResult
from datetime import datetime, timedelta, timezone

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_get_matches_empty():
    """Test getting matches when database is empty."""
    response = client.get("/api/matches/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["matches"] == []


def test_get_matches_with_data():
    """Test getting matches with sample data."""
    # Create test data
    db = TestingSessionLocal()
    
    # Create teams
    team1 = Team(
        name="Manchester United",
        league="ENG_PL",
        current_points=45,
        current_gd=15,
        current_rank=3,
        recent_form="WWDWL",
        home_win_rate=0.65,
        away_win_rate=0.45
    )
    team2 = Team(
        name="Liverpool",
        league="ENG_PL",
        current_points=50,
        current_gd=20,
        current_rank=2,
        recent_form="WWWDW",
        home_win_rate=0.70,
        away_win_rate=0.55
    )
    db.add(team1)
    db.add(team2)
    db.commit()
    
    # Create match
    match = Match(
        league="ENG_PL",
        match_date=datetime.now(timezone.utc) + timedelta(days=1),
        status=MatchStatus.SCHEDULED,
        home_team_id=team1.id,
        away_team_id=team2.id,
        odds_home=2.5,
        odds_draw=3.2,
        odds_away=2.8
    )
    db.add(match)
    db.commit()
    db.close()
    
    # Test API
    response = client.get("/api/matches/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["matches"]) == 1
    assert data["matches"][0]["league"] == "ENG_PL"


def test_get_match_detail():
    """Test getting single match detail."""
    # Create test data
    db = TestingSessionLocal()
    
    team1 = Team(name="Arsenal", league="ENG_PL", current_points=40, current_gd=10)
    team2 = Team(name="Chelsea", league="ENG_PL", current_points=38, current_gd=8)
    db.add(team1)
    db.add(team2)
    db.commit()
    
    match = Match(
        league="ENG_PL",
        match_date=datetime.now(timezone.utc),
        status=MatchStatus.SCHEDULED,
        home_team_id=team1.id,
        away_team_id=team2.id,
        odds_home=2.0,
        odds_draw=3.0,
        odds_away=3.5
    )
    db.add(match)
    db.commit()
    match_id = match.id
    db.close()
    
    # Test API
    response = client.get(f"/api/matches/{match_id}")
    assert response.status_code == 200
    data = response.json()
    assert "match" in data
    assert "home_team" in data
    assert "away_team" in data


def test_get_match_detail_not_found():
    """Test getting non-existent match."""
    response = client.get("/api/matches/9999")
    assert response.status_code == 404


def test_create_prediction():
    """Test creating a prediction."""
    # Create test data
    db = TestingSessionLocal()
    
    team1 = Team(name="Bayern Munich", league="GER_B1", current_points=60, current_gd=35)
    team2 = Team(name="Borussia Dortmund", league="GER_B1", current_points=55, current_gd=25)
    db.add(team1)
    db.add(team2)
    db.commit()
    
    match = Match(
        league="GER_B1",
        match_date=datetime.now(timezone.utc) + timedelta(days=2),
        status=MatchStatus.SCHEDULED,
        home_team_id=team1.id,
        away_team_id=team2.id,
        odds_home=1.8,
        odds_draw=3.5,
        odds_away=4.0
    )
    db.add(match)
    db.commit()
    match_id = match.id
    db.close()
    
    # Test API - should create prediction
    response = client.get(f"/api/predictions/{match_id}")
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "betting" in data
    assert "analysis" in data
    
    # Test API again - should return existing prediction
    response2 = client.get(f"/api/predictions/{match_id}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data["id"] == data2["id"]


def test_get_prediction_not_found():
    """Test getting prediction for non-existent match."""
    response = client.get("/api/predictions/9999")
    assert response.status_code == 404


def test_get_history_empty():
    """Test getting prediction history when empty."""
    response = client.get("/api/history/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["accuracy"] == 0


def test_get_history_with_predictions():
    """Test getting prediction history with data."""
    # Create test data
    db = TestingSessionLocal()
    
    team1 = Team(name="Real Madrid", league="ESP_L1", current_points=70, current_gd=40)
    team2 = Team(name="Barcelona", league="ESP_L1", current_points=68, current_gd=38)
    db.add(team1)
    db.add(team2)
    db.commit()
    
    match = Match(
        league="ESP_L1",
        match_date=datetime.now(timezone.utc) - timedelta(days=1),
        status=MatchStatus.FINISHED,
        home_team_id=team1.id,
        away_team_id=team2.id,
        home_score=2,
        away_score=1,
        odds_home=2.2,
        odds_draw=3.0,
        odds_away=3.5
    )
    db.add(match)
    db.commit()
    
    prediction = Prediction(
        match_id=match.id,
        predicted_result=PredictionResult.HOME_WIN,
        confidence_home=0.55,
        confidence_draw=0.25,
        confidence_away=0.20,
        ai_score=7.5,
        betting_advice="建議投注主勝",
        value_rating=6.8,
        llm_analysis="主隊實力較強",
        news_sentiment=0.3,
        actual_result=PredictionResult.HOME_WIN,
        is_correct=True
    )
    db.add(prediction)
    db.commit()
    db.close()
    
    # Test API
    response = client.get("/api/history/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["correct"] == 1
    assert data["accuracy"] == 100.0


def test_matches_filter_by_league():
    """Test filtering matches by league."""
    # Create test data in different leagues
    db = TestingSessionLocal()
    
    team1 = Team(name="Team EPL 1", league="ENG_PL")
    team2 = Team(name="Team EPL 2", league="ENG_PL")
    team3 = Team(name="Team BUN 1", league="GER_B1")
    team4 = Team(name="Team BUN 2", league="GER_B1")
    db.add_all([team1, team2, team3, team4])
    db.commit()
    
    match1 = Match(
        league="ENG_PL",
        match_date=datetime.now(timezone.utc),
        home_team_id=team1.id,
        away_team_id=team2.id,
        odds_home=2.0, odds_draw=3.0, odds_away=3.5
    )
    match2 = Match(
        league="GER_B1",
        match_date=datetime.now(timezone.utc),
        home_team_id=team3.id,
        away_team_id=team4.id,
        odds_home=2.0, odds_draw=3.0, odds_away=3.5
    )
    db.add_all([match1, match2])
    db.commit()
    db.close()
    
    # Test filtering
    response = client.get("/api/matches/?league=ENG_PL")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["matches"][0]["league"] == "ENG_PL"
