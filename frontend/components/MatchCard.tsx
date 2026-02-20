import Link from 'next/link'
import { formatDate, getConfidenceColor } from '@/lib/utils'

interface MatchCardProps {
  id: number
  homeTeam: string
  awayTeam: string
  league: string
  matchDate: string
  aiConfidence: number
}

export default function MatchCard({
  id,
  homeTeam,
  awayTeam,
  league,
  matchDate,
  aiConfidence,
}: MatchCardProps) {
  return (
    <Link href={`/match/${id}`}>
      <div className="bg-surface border border-gray-800 rounded-xl p-5 hover:border-primary hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 cursor-pointer group">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-text-secondary bg-gray-800 px-2 py-1 rounded-full">{league}</span>
          <span className="text-xs text-text-secondary">{formatDate(matchDate)}</span>
        </div>

        <div className="flex items-center justify-between my-4">
          <div className="text-center flex-1">
            <p className="text-text-primary font-semibold text-sm group-hover:text-primary transition-colors">
              {homeTeam}
            </p>
            <p className="text-xs text-text-secondary mt-1">主隊</p>
          </div>

          <div className="text-center px-4">
            <span className="text-2xl font-bold text-text-secondary">VS</span>
          </div>

          <div className="text-center flex-1">
            <p className="text-text-primary font-semibold text-sm group-hover:text-primary transition-colors">
              {awayTeam}
            </p>
            <p className="text-xs text-text-secondary mt-1">客隊</p>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-3 mt-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-text-secondary">AI 推薦指數</span>
            <span className={`text-sm font-bold ${getConfidenceColor(aiConfidence)}`}>
              {Math.round(aiConfidence * 100)}%
            </span>
          </div>
          <div className="mt-2 bg-gray-800 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-500 ${
                aiConfidence >= 0.7 ? 'bg-primary' : aiConfidence >= 0.5 ? 'bg-accent' : 'bg-red-500'
              }`}
              style={{ width: `${aiConfidence * 100}%` }}
            />
          </div>
        </div>
      </div>
    </Link>
  )
}
