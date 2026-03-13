import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Prediction {
  date: string;
  time: string;
  league: string;
  home_team: string;
  away_team: string;
  prediction: {
    prediction: 'home_win' | 'draw' | 'away_win';
    confidence: number;
    probabilities: {
      home_win: number;
      draw: number;
      away_win: number;
    };
    expected_score: string;
    analysis: {
      home_total_score: number;
      away_total_score: number;
      home_form: string;
      away_form: string;
      home_win_rate: number;
      away_win_rate: number;
      home_avg_goals: number;
      away_avg_goals: number;
      home_form_score: number;
      away_form_score: number;
    };
  };
  ai_analysis?: string;
}

export interface PredictionsResponse {
  total: number;
  predictions: Prediction[];
}

export interface LeaguesResponse {
  leagues: string[];
  count: number;
}

export interface TeamsResponse {
  teams: string[];
  count: number;
}

export interface TeamDetails {
  name: string;
  league: string;
  matches_played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_scored: number;
  goals_conceded: number;
  recent_form: string;
  home_win_rate: number;
  away_win_rate: number;
}

export const predictionService = {
  async getPredictions(params: {
    league?: string;
    team?: string;
    date?: string;
  } = {}): Promise<PredictionsResponse> {
    const response = await api.get('/api/predictions/', { params });
    return response.data;
  },

  async getLeagues(): Promise<LeaguesResponse> {
    const response = await api.get('/api/predictions/leagues');
    return response.data;
  },

  async getTeams(league?: string): Promise<TeamsResponse> {
    const params = league ? { league } : {};
    const response = await api.get('/api/predictions/teams', { params });
    return response.data;
  },

  async getTeamDetails(teamName: string): Promise<TeamDetails | null> {
    try {
      // 從所有預測中找到該球隊的資料
      const response = await api.get('/api/predictions/', { 
        params: { team: teamName } 
      });
      
      if (response.data.predictions.length > 0) {
        const prediction = response.data.predictions[0];
        const isHome = prediction.home_team === teamName;
        const analysis = prediction.prediction.analysis;
        
        return {
          name: teamName,
          league: prediction.league,
          matches_played: 0, // TODO: 從後端取得
          wins: 0,
          draws: 0,
          losses: 0,
          goals_scored: 0,
          goals_conceded: 0,
          recent_form: isHome ? analysis.home_form : analysis.away_form,
          home_win_rate: isHome ? analysis.home_win_rate : 0,
          away_win_rate: !isHome ? analysis.away_win_rate : 0,
        };
      }
      return null;
    } catch (error) {
      console.error('Error fetching team details:', error);
      return null;
    }
  },

  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};
