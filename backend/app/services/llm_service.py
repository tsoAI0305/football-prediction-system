"""LLM service for match analysis."""
from typing import Dict
from app.config import settings


class LLMService:
    """LLM service for analyzing matches using AI."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model = settings.LLM_MODEL
        self.enabled = bool(self.api_key and self.api_key != "your_groq_api_key_here")
    
    async def analyze_match(self, home_team: str, away_team: str) -> Dict:
        """
        Analyze match using LLM for insights and sentiment.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            Dictionary containing:
                - analysis: LLM-generated analysis text
                - sentiment: Sentiment score (-1 to 1)
        """
        if not self.enabled:
            return self._get_mock_analysis(home_team, away_team)
        
        try:
            # In production, this would call actual LLM API
            # For now, return mock data
            return self._get_mock_analysis(home_team, away_team)
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return self._get_mock_analysis(home_team, away_team)
    
    def _get_mock_analysis(self, home_team: str, away_team: str) -> Dict:
        """
        Generate mock LLM analysis.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            Mock analysis dictionary
        """
        analysis = f"""
【AI 深度分析】

本場比賽 {home_team} 主場迎戰 {away_team}。

根據雙方近期表現和歷史交鋒記錄，主隊在主場具有一定優勢。
主隊近期狀態穩定，防守端表現出色，而客隊在客場作戰能力略顯不足。

預測本場比賽將是一場激烈的對抗，主隊有較大機會取得勝利。

建議：關注主隊的進攻效率和客隊的防守表現。
        """.strip()
        
        # Mock sentiment: slightly positive for home team
        sentiment = 0.3
        
        return {
            'analysis': analysis,
            'sentiment': sentiment
        }
