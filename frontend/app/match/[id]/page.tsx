import { getMatchDetails, getPrediction } from '@/lib/api'
import { mockMatches, mockPredictions, mockTeamStats } from '@/lib/mockData'
import { formatDate } from '@/lib/utils'
import PredictionPanel from '@/components/PredictionPanel'
import StatsChart from '@/components/StatsChart'
import ErrorMessage from '@/components/ErrorMessage'
import Link from 'next/link'

interface PageProps {
  params: Promise<{ id: string }>
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params
  const matchId = parseInt(id)
  const match = mockMatches.find((m) => m.id === matchId)
  return {
    title: match
      ? `${match.home_team} vs ${match.away_team} - Football AI Predictor`
      : 'Match Details - Football AI Predictor',
  }
}

export default async function MatchDetailPage({ params }: PageProps) {
  const { id } = await params
  const matchId = parseInt(id)

  let match = null
  let prediction = null

  try {
    match = await getMatchDetails(matchId)
    prediction = await getPrediction(matchId)
  } catch {
    // fall through to mock data
  }

  // Fall back to mock data
  if (!match) {
    match = mockMatches.find((m) => m.id === matchId) ?? null
  }
  if (!prediction) {
    prediction = mockPredictions[matchId] ?? null
  }

  if (!match) {
    return <ErrorMessage message="找不到比賽資訊" />
  }

  const homeStats = mockTeamStats[match.home_team]
  const awayStats = mockTeamStats[match.away_team]

  return (
    <div>
      <Link
        href="/"
        className="inline-flex items-center text-text-secondary hover:text-primary transition-colors mb-6"
      >
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        返回首頁
      </Link>

      {/* Match Header */}
      <div className="bg-surface border border-gray-800 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs text-text-secondary bg-gray-800 px-2 py-1 rounded-full">
            {match.league}
          </span>
          <span className="text-xs text-text-secondary">{formatDate(match.match_date)}</span>
          {match.status === 'live' && (
            <span className="text-xs text-red-400 bg-red-900/30 px-2 py-1 rounded-full animate-pulse">
              LIVE
            </span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <h2 className="text-2xl font-bold text-text-primary">{match.home_team}</h2>
            <p className="text-sm text-text-secondary mt-1">主隊</p>
            {match.status === 'finished' && match.home_score !== undefined && (
              <p className="text-4xl font-bold text-primary mt-2">{match.home_score}</p>
            )}
          </div>

          <div className="text-center px-6">
            {match.status === 'finished' ? (
              <span className="text-text-secondary text-sm">終場</span>
            ) : (
              <span className="text-3xl font-bold text-text-secondary">VS</span>
            )}
          </div>

          <div className="text-center flex-1">
            <h2 className="text-2xl font-bold text-text-primary">{match.away_team}</h2>
            <p className="text-sm text-text-secondary mt-1">客隊</p>
            {match.status === 'finished' && match.away_score !== undefined && (
              <p className="text-4xl font-bold text-secondary mt-2">{match.away_score}</p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prediction Panel */}
        {prediction ? (
          <PredictionPanel prediction={prediction} />
        ) : (
          <div className="bg-surface border border-gray-800 rounded-xl p-6">
            <p className="text-text-secondary text-center">尚無預測資料</p>
          </div>
        )}

        {/* Stats Chart */}
        {homeStats && awayStats ? (
          <StatsChart homeStats={homeStats} awayStats={awayStats} />
        ) : (
          <div className="bg-surface border border-gray-800 rounded-xl p-6">
            <p className="text-text-secondary text-center">尚無球隊統計資料</p>
          </div>
        )}
      </div>
    </div>
  )
}
