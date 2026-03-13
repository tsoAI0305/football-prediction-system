"""Match model for database."""
from sqlalchemy import Column, Integer, String, DateTime, Float
from app.database import Base
from datetime import datetime, timezone


class Match(Base):
    """Match model representing football matches."""
    
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    league = Column(String, index=True)
    match_date = Column(DateTime, index=True)
    status = Column(String, default="scheduled")
    
    # 直接儲存球隊名稱（主要使用）
    home_team = Column(String, nullable=True, index=True)
    away_team = Column(String, nullable=True, index=True)
    
    # Team ID references (保留但不用外鍵)
    home_team_id = Column(Integer, nullable=True)
    away_team_id = Column(Integer, nullable=True)
    
    # Match scores
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # 比賽統計數據
    home_shots = Column(Integer, nullable=True)
    away_shots = Column(Integer, nullable=True)
    home_shots_on_target = Column(Integer, nullable=True)
    away_shots_on_target = Column(Integer, nullable=True)
    home_corners = Column(Integer, nullable=True)
    away_corners = Column(Integer, nullable=True)
    home_fouls = Column(Integer, nullable=True)
    away_fouls = Column(Integer, nullable=True)
    home_yellow = Column(Integer, nullable=True)
    away_yellow = Column(Integer, nullable=True)
    home_red = Column(Integer, nullable=True)
    away_red = Column(Integer, nullable=True)
    
    # API 整合
    api_fixture_id = Column(Integer, nullable=True, unique=True, index=True)
    
    # Odds data
    odds_home = Column(Float, nullable=True)
    odds_draw = Column(Float, nullable=True)
    odds_away = Column(Float, nullable=True)
    
    # 更多賠率數據
    b365_home = Column(Float, nullable=True)
    b365_draw = Column(Float, nullable=True)
    b365_away = Column(Float, nullable=True)
    avg_home = Column(Float, nullable=True)
    avg_draw = Column(Float, nullable=True)
    avg_away = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 移除 predictions 關聯，避免循環導入和複雜性問題
    # 如需查詢 predictions，直接使用 db.query(Prediction).filter(Prediction.match_id == match.id)
    
    def __repr__(self):
        """String representation."""
        home = self.home_team or 'N/A'
        away = self.away_team or 'N/A'
        return f"<Match(id={self.id}, {home} vs {away})>"
    
    @property
    def home_team_name(self):
        """Get home team name."""
        return self.home_team
    
    @property
    def away_team_name(self):
        """Get away team name."""
        return self.away_team
    
    @property
    def result(self):
        """Get match result (H/D/A)."""
        if self.home_score is None or self.away_score is None:
            return None
        if self.home_score > self.away_score:
            return 'H'
        elif self.home_score < self.away_score:
            return 'A'
        else:
            return 'D'