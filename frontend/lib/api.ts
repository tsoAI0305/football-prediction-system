import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// ── 型別定義 ───────────────────────────────────────────────────────────────

export interface PredictionDetail {
  prediction: 'H' | 'D' | 'A';
  confidence: number;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  over25_prob: number;
  under25_prob: number;
  ou_pick: 'OVER' | 'UNDER';
  betting_advice: string;
}

export interface Prediction {
  match_id: number;
  league: string;
  date: string;
  time: string;
  home_team: string;
  away_team: string;
  prediction: PredictionDetail;
  generated_at: string;
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

export interface Injury {
  player: string;
  position: string;
  info: string;
  expected_return: string;
}

export interface TopPlayer {
  player_name: string;
  stat_type: 'rating' | 'goals' | 'assists';
  goals: number;
  assists: number;
  rating: number;
}

export interface LineupPlayer {
  player_name: string;
  goals: number;
  assists: number;
  rating: number;
}

// ── Phase 3: Tactical profile types ───────────────────────────────────────────

export interface StyleInfo {
  key: string;
  label_zh: string;
  emoji: string;
  badge_class: string;
}

export interface TacticalMetrics {
  goals_for_pg: number;
  goals_against_pg: number;
  win_rate: number;
  draw_rate: number;
  points_pg: number;
  shots_pg: number | null;
  sot_pg: number | null;
  fouls_pg: number | null;
  corners_pg: number | null;
  db_matches: number;
}

export interface TacticalProfile {
  style_labels: string[];
  style_info: StyleInfo[];
  formation: string;
  alternate_formations: string[];
  metrics: TacticalMetrics;
  style_evidence: string[];
  tactical_dna: string;
}

export interface FormationRow {
  label: string;
  count: number;
  players: LineupPlayer[];
}

export interface LineupByFormation {
  formation: string;
  rows: FormationRow[];
}

// ──────────────────────────────────────────────────────────────────────────────

export interface TeamDetails {
  team_name: string;
  league: string;
  // standings
  rank: number;
  points: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  played: number;
  // form & rates
  recent_form: string;
  home_win_rate: number;
  away_win_rate: number;
  avg_goals: number;
  // ranking-card scores
  total_score: number;
  home_score: number;
  away_score: number;
  overall_ranking: number;
  total_teams: number;
  upcoming_matches: number;
  // enriched
  injuries: Injury[];
  top_players: TopPlayer[];
  lineup: LineupPlayer[];
  // Phase 3
  tactical_profile: TacticalProfile | null;
  lineup_by_formation: LineupByFormation | null;
}

export interface HistoryRecord {
  id: number;
  match_id: number | null;
  date: string | null;
  time: string | null;
  league: string | null;
  home_team: string | null;
  away_team: string | null;
  predicted_result: 'H' | 'D' | 'A' | null;
  predicted_ou: 'OVER' | 'UNDER' | null;
  confidence: number | null;
  over25_prob: number | null;
  actual_home_score: number | null;
  actual_away_score: number | null;
  actual_result: 'H' | 'D' | 'A' | null;
  is_correct: boolean | null;
  ou_hit: boolean | null;
}

export interface HistoryResponse {
  total: number;
  completed: number;
  correct: number;
  accuracy: number;
  ou_correct: number;
  ou_accuracy: number;
  records: HistoryRecord[];
}

// ── 輔助函數 ───────────────────────────────────────────────────────────────

export const resultLabel = (r: 'H' | 'D' | 'A') =>
  ({ H: '主勝', D: '平局', A: '客勝' }[r]);

export const resultKey = (r: 'H' | 'D' | 'A') =>
  ({ H: 'home_win', D: 'draw', A: 'away_win' }[r]);

export const confidencePct = (c: number) => `${Math.round(c * 100)}%`;

// ── API 服務物件 ───────────────────────────────────────────────────────────

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

  async getStats() {
    const response = await api.get('/api/predictions/stats');
    return response.data;
  },

  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};

// ── 獨立 export 函數（供各 page 直接 import）──────────────────────────────

export async function getHistory(params: {
  limit?: number;
  only_completed?: boolean;
} = {}): Promise<HistoryResponse> {
  const response = await api.get('/api/history/', { params });
  return response.data;
}

export async function getTeamMatches(teamName: string): Promise<Prediction[]> {
  const response = await api.get('/api/predictions/', {
    params: { team: teamName },
  });
  return response.data.predictions ?? [];
}

export async function getTeamDetails(teamName: string): Promise<TeamDetails> {
  const response = await api.get(`/api/teams/${encodeURIComponent(teamName)}`);
  return response.data;
}