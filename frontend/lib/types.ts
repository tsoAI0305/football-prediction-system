export interface Match {
  id: number
  home_team: string
  away_team: string
  league: string
  match_date: string
  status: 'upcoming' | 'live' | 'finished'
  home_score?: number
  away_score?: number
}

export interface Prediction {
  match_id: number
  home_win_prob: number
  draw_prob: number
  away_win_prob: number
  confidence_score: number
  llm_analysis: string
  recommended_bet?: string
}

export interface TeamStats {
  team_name: string
  wins: number
  draws: number
  losses: number
  goals_scored: number
  goals_conceded: number
  form: string[]
}

export interface MatchDetail extends Match {
  prediction?: Prediction
  home_stats?: TeamStats
  away_stats?: TeamStats
  head_to_head?: HeadToHead[]
}

export interface HeadToHead {
  date: string
  home_team: string
  away_team: string
  home_score: number
  away_score: number
}

export interface HistoryRecord {
  id: number
  match: Match
  prediction: Prediction
  actual_result?: string
  is_correct?: boolean
}
