import { getMatches } from '@/lib/api'
import { mockMatches, mockPredictions } from '@/lib/mockData'
import { Match } from '@/lib/types'
import MatchCard from '@/components/MatchCard'
import { EmptyState } from '@/components/ErrorMessage'

export const metadata = {
  title: 'Football AI Predictor - 首頁',
  description: '查看即將進行的足球比賽和 AI 預測',
}

export default async function HomePage() {
  let matches: Match[] | null = null

  try {
    matches = await getMatches()
  } catch {
    matches = null
  }

  // Fall back to mock data if API not available
  const displayMatches = matches ?? mockMatches

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">即將進行的比賽</h1>
        <p className="text-text-secondary">由 AI 分析並預測比賽結果</p>
      </div>

      {displayMatches.length === 0 ? (
        <EmptyState message="目前沒有即將進行的比賽" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayMatches.map((match) => {
            const prediction = mockPredictions[match.id]
            return (
              <MatchCard
                key={match.id}
                id={match.id}
                homeTeam={match.home_team}
                awayTeam={match.away_team}
                league={match.league}
                matchDate={match.match_date}
                aiConfidence={prediction?.confidence_score ?? 0.5}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
