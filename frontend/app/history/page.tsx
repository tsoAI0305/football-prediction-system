import { getHistory } from '@/lib/api'
import { mockHistory } from '@/lib/mockData'
import { HistoryRecord } from '@/lib/types'
import { formatDate, getConfidenceColor } from '@/lib/utils'
import { EmptyState } from '@/components/ErrorMessage'
import Link from 'next/link'

export const metadata = {
  title: 'Football AI Predictor - 歷史記錄',
  description: '查看過往預測記錄和準確率',
}

export default async function HistoryPage() {
  let history: HistoryRecord[] | null = null

  try {
    history = await getHistory()
  } catch {
    history = null
  }

  const displayHistory = history ?? mockHistory

  const correctCount = displayHistory.filter((r) => r.is_correct).length
  const accuracy =
    displayHistory.length > 0 ? Math.round((correctCount / displayHistory.length) * 100) : 0

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">歷史預測記錄</h1>
        <p className="text-text-secondary">過往比賽預測結果統計</p>
      </div>

      {/* Accuracy Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-surface border border-gray-800 rounded-xl p-5 text-center">
          <p className="text-3xl font-bold text-primary">{accuracy}%</p>
          <p className="text-sm text-text-secondary mt-1">整體準確率</p>
        </div>
        <div className="bg-surface border border-gray-800 rounded-xl p-5 text-center">
          <p className="text-3xl font-bold text-text-primary">{displayHistory.length}</p>
          <p className="text-sm text-text-secondary mt-1">總預測場次</p>
        </div>
        <div className="bg-surface border border-gray-800 rounded-xl p-5 text-center">
          <p className="text-3xl font-bold text-accent">{correctCount}</p>
          <p className="text-sm text-text-secondary mt-1">預測正確</p>
        </div>
      </div>

      {displayHistory.length === 0 ? (
        <EmptyState message="目前沒有歷史記錄" />
      ) : (
        <div className="space-y-4">
          {displayHistory.map((record) => (
            <Link href={`/match/${record.match.id}`} key={record.id}>
              <div className="bg-surface border border-gray-800 rounded-xl p-5 hover:border-primary transition-all duration-300">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-text-secondary bg-gray-800 px-2 py-1 rounded-full">
                      {record.match.league}
                    </span>
                    <span className="text-xs text-text-secondary">{formatDate(record.match.match_date)}</span>
                  </div>
                  {record.is_correct !== undefined && (
                    <span
                      className={`text-xs font-bold px-2 py-1 rounded-full ${
                        record.is_correct
                          ? 'text-primary bg-primary/10'
                          : 'text-red-400 bg-red-900/20'
                      }`}
                    >
                      {record.is_correct ? '✓ 預測正確' : '✗ 預測錯誤'}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between mb-3">
                  <div className="flex-1 text-center">
                    <p className="text-text-primary font-semibold">{record.match.home_team}</p>
                    {record.match.home_score !== undefined && (
                      <p className="text-2xl font-bold text-primary">{record.match.home_score}</p>
                    )}
                  </div>
                  <div className="px-4 text-text-secondary">
                    {record.match.status === 'finished' ? 'FT' : 'VS'}
                  </div>
                  <div className="flex-1 text-center">
                    <p className="text-text-primary font-semibold">{record.match.away_team}</p>
                    {record.match.away_score !== undefined && (
                      <p className="text-2xl font-bold text-secondary">{record.match.away_score}</p>
                    )}
                  </div>
                </div>

                <div className="border-t border-gray-800 pt-3 flex items-center justify-between">
                  <div className="flex gap-4 text-xs text-text-secondary">
                    <span>主勝 {Math.round(record.prediction.home_win_prob * 100)}%</span>
                    <span>平局 {Math.round(record.prediction.draw_prob * 100)}%</span>
                    <span>客勝 {Math.round(record.prediction.away_win_prob * 100)}%</span>
                  </div>
                  <span className={`text-xs font-bold ${getConfidenceColor(record.prediction.confidence_score)}`}>
                    AI: {Math.round(record.prediction.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
