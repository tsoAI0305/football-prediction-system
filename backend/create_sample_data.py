"""Sample data script to populate the database for testing."""
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.team import Team
from app.models.match import Match, MatchStatus
from app.models.prediction import Prediction, PredictionResult
from datetime import datetime, timedelta, timezone


def create_sample_data():
    """Create sample data for testing the API."""
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Create teams
        teams_data = [
            # English Premier League
            {"name": "Manchester United", "league": "ENG_PL", "points": 45, "gd": 15, "rank": 3, "form": "WWDWL", "home_wr": 0.65, "away_wr": 0.45},
            {"name": "Liverpool", "league": "ENG_PL", "points": 50, "gd": 20, "rank": 2, "form": "WWWDW", "home_wr": 0.70, "away_wr": 0.55},
            {"name": "Arsenal", "league": "ENG_PL", "points": 52, "gd": 22, "rank": 1, "form": "WWWWL", "home_wr": 0.72, "away_wr": 0.58},
            {"name": "Chelsea", "league": "ENG_PL", "points": 42, "gd": 12, "rank": 4, "form": "WDWLL", "home_wr": 0.60, "away_wr": 0.40},
            {"name": "Manchester City", "league": "ENG_PL", "points": 48, "gd": 18, "rank": 2, "form": "WWDWW", "home_wr": 0.68, "away_wr": 0.52},
            
            # German Bundesliga
            {"name": "Bayern Munich", "league": "GER_B1", "points": 60, "gd": 35, "rank": 1, "form": "WWWWW", "home_wr": 0.80, "away_wr": 0.65},
            {"name": "Borussia Dortmund", "league": "GER_B1", "points": 55, "gd": 25, "rank": 2, "form": "WWDWL", "home_wr": 0.72, "away_wr": 0.58},
            {"name": "RB Leipzig", "league": "GER_B1", "points": 50, "gd": 18, "rank": 3, "form": "WDWDW", "home_wr": 0.65, "away_wr": 0.50},
            
            # Spanish La Liga
            {"name": "Real Madrid", "league": "ESP_L1", "points": 65, "gd": 40, "rank": 1, "form": "WWWWW", "home_wr": 0.82, "away_wr": 0.68},
            {"name": "Barcelona", "league": "ESP_L1", "points": 62, "gd": 38, "rank": 2, "form": "WWWDW", "home_wr": 0.78, "away_wr": 0.62},
        ]
        
        teams = []
        for team_data in teams_data:
            team = Team(
                name=team_data["name"],
                league=team_data["league"],
                current_points=team_data["points"],
                current_gd=team_data["gd"],
                current_rank=team_data["rank"],
                recent_form=team_data["form"],
                home_win_rate=team_data["home_wr"],
                away_win_rate=team_data["away_wr"]
            )
            teams.append(team)
        
        db.add_all(teams)
        db.commit()
        print(f"✅ Created {len(teams)} teams")
        
        # Create upcoming matches
        matches = []
        now = datetime.now(timezone.utc)
        
        # English Premier League matches
        matches.append(Match(
            league="ENG_PL",
            match_date=now + timedelta(days=1, hours=15),
            status=MatchStatus.SCHEDULED,
            home_team_id=teams[0].id,  # Man Utd
            away_team_id=teams[1].id,  # Liverpool
            odds_home=2.5,
            odds_draw=3.2,
            odds_away=2.8
        ))
        
        matches.append(Match(
            league="ENG_PL",
            match_date=now + timedelta(days=2, hours=12),
            status=MatchStatus.SCHEDULED,
            home_team_id=teams[2].id,  # Arsenal
            away_team_id=teams[3].id,  # Chelsea
            odds_home=2.0,
            odds_draw=3.5,
            odds_away=3.8
        ))
        
        matches.append(Match(
            league="ENG_PL",
            match_date=now + timedelta(days=2, hours=17),
            status=MatchStatus.SCHEDULED,
            home_team_id=teams[4].id,  # Man City
            away_team_id=teams[0].id,  # Man Utd
            odds_home=1.6,
            odds_draw=4.0,
            odds_away=5.5
        ))
        
        # German Bundesliga matches
        matches.append(Match(
            league="GER_B1",
            match_date=now + timedelta(days=3, hours=18),
            status=MatchStatus.SCHEDULED,
            home_team_id=teams[5].id,  # Bayern
            away_team_id=teams[6].id,  # Dortmund
            odds_home=1.8,
            odds_draw=3.8,
            odds_away=4.2
        ))
        
        matches.append(Match(
            league="GER_B1",
            match_date=now + timedelta(days=3, hours=15),
            status=MatchStatus.SCHEDULED,
            home_team_id=teams[7].id,  # Leipzig
            away_team_id=teams[5].id,  # Bayern
            odds_home=4.5,
            odds_draw=3.8,
            odds_away=1.7
        ))
        
        # Spanish La Liga match
        matches.append(Match(
            league="ESP_L1",
            match_date=now + timedelta(days=4, hours=20),
            status=MatchStatus.SCHEDULED,
            home_team_id=teams[8].id,  # Real Madrid
            away_team_id=teams[9].id,  # Barcelona
            odds_home=2.2,
            odds_draw=3.3,
            odds_away=3.1
        ))
        
        # Add a finished match with result
        finished_match = Match(
            league="ENG_PL",
            match_date=now - timedelta(days=2),
            status=MatchStatus.FINISHED,
            home_team_id=teams[1].id,  # Liverpool
            away_team_id=teams[3].id,  # Chelsea
            home_score=3,
            away_score=1,
            odds_home=1.9,
            odds_draw=3.5,
            odds_away=4.0
        )
        matches.append(finished_match)
        
        db.add_all(matches)
        db.commit()
        print(f"✅ Created {len(matches)} matches")
        
        # Create a prediction for the finished match
        prediction = Prediction(
            match_id=finished_match.id,
            predicted_result=PredictionResult.HOME_WIN,
            confidence_home=0.62,
            confidence_draw=0.23,
            confidence_away=0.15,
            ai_score=8.2,
            betting_advice="強烈推薦投注主勝（信心度: 62.0%）",
            value_rating=7.5,
            llm_analysis="利物浦在主場表現出色，近期狀態良好。切爾西客場作戰能力較弱，預計主隊會取得勝利。",
            news_sentiment=0.4,
            actual_result=PredictionResult.HOME_WIN,
            is_correct=True
        )
        db.add(prediction)
        db.commit()
        print(f"✅ Created 1 prediction with actual result")
        
        print("\n🎉 Sample data created successfully!")
        print(f"   - {len(teams)} teams")
        print(f"   - {len(matches)} matches (including {sum(1 for m in matches if m.status == MatchStatus.FINISHED)} finished)")
        print(f"   - 1 prediction")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
