import { TeamStats } from '@/lib/types'
import { getFormColor } from '@/lib/utils'

interface StatsChartProps {
  homeStats: TeamStats
  awayStats: TeamStats
}

export default function StatsChart({ homeStats, awayStats }: StatsChartProps) {
  const totalGames = (stats: TeamStats) => stats.wins + stats.draws + stats.losses
  const winRate = (stats: TeamStats) => {
    const total = totalGames(stats)
    return total > 0 ? Math.round((stats.wins / total) * 100) : 0
  }

  const statRows = [
    { label: '勝場', home: homeStats.wins, away: awayStats.wins },
    { label: '平場', home: homeStats.draws, away: awayStats.draws },
    { label: '敗場', home: homeStats.losses, away: awayStats.losses },
    { label: '進球', home: homeStats.goals_scored, away: awayStats.goals_scored },
    { label: '失球', home: homeStats.goals_conceded, away: awayStats.goals_conceded },
    { label: '勝率', home: `${winRate(homeStats)}%`, away: `${winRate(awayStats)}%` },
  ]

  return (
    <div className="bg-surface border border-gray-800 rounded-xl p-6">
      <h2 className="text-xl font-bold text-text-primary mb-6">球隊數據對比</h2>

      <div className="grid grid-cols-3 gap-4 mb-4 text-center">
        <div className="text-sm font-semibold text-primary">{homeStats.team_name}</div>
        <div className="text-xs text-text-secondary">統計項目</div>
        <div className="text-sm font-semibold text-secondary">{awayStats.team_name}</div>
      </div>

      <div className="space-y-3">
        {statRows.map(({ label, home, away }) => (
          <div key={label} className="grid grid-cols-3 gap-4 text-center">
            <div className="text-sm text-text-primary font-medium">{home}</div>
            <div className="text-xs text-text-secondary">{label}</div>
            <div className="text-sm text-text-primary font-medium">{away}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        {[homeStats, awayStats].map((stats, i) => (
          <div key={stats.team_name}>
            <p className="text-xs text-text-secondary mb-2">近況 ({i === 0 ? '主隊' : '客隊'})</p>
            <div className="flex gap-1">
              {stats.form.map((result, idx) => (
                <span
                  key={idx}
                  className={`${getFormColor(result)} w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white`}
                >
                  {result}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
