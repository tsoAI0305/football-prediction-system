import os
from typing import Optional, Dict
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMAnalysisService:
    """
    LLM Analysis Service using Groq API for football match analysis
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing Groq client: {e}")
    
    def analyze_match(
        self,
        home_team_name: str,
        away_team_name: str,
        home_team_stats: Dict,
        away_team_stats: Dict,
        prediction_probs: Dict[str, float],
        model: str = "mixtral-8x7b-32768"
    ) -> Optional[str]:
        """
        Generate LLM-powered analysis of the match prediction
        
        Args:
            home_team_name: Name of the home team
            away_team_name: Name of the away team
            home_team_stats: Home team statistics
            away_team_stats: Away team statistics
            prediction_probs: Prediction probabilities (home_win, draw, away_win)
            model: Groq model to use
        
        Returns:
            Analysis text or None if unavailable
        """
        if not self.client:
            return self._fallback_analysis(
                home_team_name, away_team_name, 
                home_team_stats, away_team_stats, 
                prediction_probs
            )
        
        try:
            # Construct the prompt
            prompt = self._construct_analysis_prompt(
                home_team_name, away_team_name,
                home_team_stats, away_team_stats,
                prediction_probs
            )
            
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional football analyst with expertise in match predictions and statistical analysis. Provide concise, insightful analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=model,
                temperature=0.7,
                max_tokens=500
            )
            
            return chat_completion.choices[0].message.content
        
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return self._fallback_analysis(
                home_team_name, away_team_name,
                home_team_stats, away_team_stats,
                prediction_probs
            )
    
    def _construct_analysis_prompt(
        self,
        home_team_name: str,
        away_team_name: str,
        home_team_stats: Dict,
        away_team_stats: Dict,
        prediction_probs: Dict[str, float]
    ) -> str:
        """Construct the analysis prompt for the LLM"""
        
        home_games = max(home_team_stats.get('games_played', 1), 1)
        away_games = max(away_team_stats.get('games_played', 1), 1)
        
        prompt = f"""Analyze this football match prediction:

Match: {home_team_name} (Home) vs {away_team_name} (Away)

Home Team Statistics:
- Win Rate: {home_team_stats.get('wins', 0) / home_games * 100:.1f}%
- Goals For: {home_team_stats.get('goals_for', 0)} ({home_team_stats.get('goals_for', 0) / home_games:.2f} per game)
- Goals Against: {home_team_stats.get('goals_against', 0)} ({home_team_stats.get('goals_against', 0) / home_games:.2f} per game)
- Points: {home_team_stats.get('points', 0)} ({home_team_stats.get('points', 0) / home_games:.2f} per game)

Away Team Statistics:
- Win Rate: {away_team_stats.get('wins', 0) / away_games * 100:.1f}%
- Goals For: {away_team_stats.get('goals_for', 0)} ({away_team_stats.get('goals_for', 0) / away_games:.2f} per game)
- Goals Against: {away_team_stats.get('goals_against', 0)} ({away_team_stats.get('goals_against', 0) / away_games:.2f} per game)
- Points: {away_team_stats.get('points', 0)} ({away_team_stats.get('points', 0) / away_games:.2f} per game)

AI Prediction:
- Home Win Probability: {prediction_probs.get('home_win', 0) * 100:.1f}%
- Draw Probability: {prediction_probs.get('draw', 0) * 100:.1f}%
- Away Win Probability: {prediction_probs.get('away_win', 0) * 100:.1f}%

Provide a brief analysis (3-4 sentences) covering:
1. Key factors influencing the prediction
2. Notable strengths/weaknesses of each team
3. Potential outcome and confidence level
"""
        return prompt
    
    def _fallback_analysis(
        self,
        home_team_name: str,
        away_team_name: str,
        home_team_stats: Dict,
        away_team_stats: Dict,
        prediction_probs: Dict[str, float]
    ) -> str:
        """Provide a simple rule-based analysis when LLM is unavailable"""
        
        home_games = max(home_team_stats.get('games_played', 1), 1)
        away_games = max(away_team_stats.get('games_played', 1), 1)
        
        home_ppg = home_team_stats.get('points', 0) / home_games
        away_ppg = away_team_stats.get('points', 0) / away_games
        
        home_win_prob = prediction_probs.get('home_win', 0)
        draw_prob = prediction_probs.get('draw', 0)
        away_win_prob = prediction_probs.get('away_win', 0)
        
        # Determine predicted outcome
        if home_win_prob > draw_prob and home_win_prob > away_win_prob:
            prediction = f"{home_team_name} win"
            confidence = "high" if home_win_prob > 0.5 else "moderate"
        elif away_win_prob > draw_prob and away_win_prob > home_win_prob:
            prediction = f"{away_team_name} win"
            confidence = "high" if away_win_prob > 0.5 else "moderate"
        else:
            prediction = "Draw"
            confidence = "moderate"
        
        # Form comparison
        if home_ppg > away_ppg + 0.5:
            form = f"{home_team_name} showing significantly better form"
        elif away_ppg > home_ppg + 0.5:
            form = f"{away_team_name} showing significantly better form"
        else:
            form = "Both teams in similar form"
        
        analysis = f"""Analysis: {form} with {home_team_name} averaging {home_ppg:.2f} points per game compared to {away_team_name}'s {away_ppg:.2f}. 
The prediction favors a {prediction} with {confidence} confidence ({max(home_win_prob, draw_prob, away_win_prob)*100:.1f}% probability). 
Home advantage and current statistics support this outcome."""
        
        return analysis
    
    def get_betting_insight(
        self,
        prediction_probs: Dict[str, float],
        odds: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Generate betting insights based on prediction and odds
        
        Args:
            prediction_probs: Prediction probabilities
            odds: Betting odds (home, draw, away)
        
        Returns:
            Betting insight text
        """
        if not odds:
            return "No betting odds available for analysis."
        
        home_value = self._calculate_value_bet(
            prediction_probs.get('home_win', 0),
            odds.get('home', 0)
        )
        draw_value = self._calculate_value_bet(
            prediction_probs.get('draw', 0),
            odds.get('draw', 0)
        )
        away_value = self._calculate_value_bet(
            prediction_probs.get('away_win', 0),
            odds.get('away', 0)
        )
        
        insights = []
        if home_value > 1.1:
            insights.append(f"Home win shows value ({home_value:.2f}x expected return)")
        if draw_value > 1.1:
            insights.append(f"Draw shows value ({draw_value:.2f}x expected return)")
        if away_value > 1.1:
            insights.append(f"Away win shows value ({away_value:.2f}x expected return)")
        
        if not insights:
            return "No significant value bets identified based on current odds."
        
        return "Betting insights: " + "; ".join(insights)
    
    def _calculate_value_bet(self, probability: float, odds: float) -> float:
        """Calculate value bet ratio"""
        if probability <= 0 or odds <= 0:
            return 0
        
        implied_probability = 1 / odds
        return probability / implied_probability
