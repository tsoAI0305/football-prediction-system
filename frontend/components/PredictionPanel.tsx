import { Prediction } from '@/lib/types'
import { getConfidenceColor, getConfidenceLabel } from '@/lib/utils'

interface PredictionPanelProps {
  prediction: Prediction
}

export default function PredictionPanel({ prediction }: PredictionPanelProps) {
  const { home_win_prob, draw_prob, away_win_prob, confidence_score, llm_analysis, recommended_bet } =
    prediction

  const bars = [
    { label: '主勝', prob: home_win_prob, color: 'bg-primary' },
    { label: '平局', prob: draw_prob, color: 'bg-accent' },
    { label: '客勝', prob: away_win_prob, color: 'bg-secondary' },
  ]

  return (
    <div className="bg-surface border border-gray-800 rounded-xl p-6">
      <h2 className="text-xl font-bold text-text-primary mb-2">AI 預測結果</h2>

      <div className="flex items-center gap-2 mb-6">
        <span className="text-sm text-text-secondary">信心指數：</span>
        <span className={`text-sm font-bold ${getConfidenceColor(confidence_score)}`}>
          {Math.round(confidence_score * 100)}% ({getConfidenceLabel(confidence_score)})
        </span>
      </div>

      <div className="space-y-4 mb-6">
        {bars.map(({ label, prob, color }) => (
          <div key={label}>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-text-secondary">{label}</span>
              <span className="text-sm font-bold text-text-primary">{Math.round(prob * 100)}%</span>
            </div>
            <div className="bg-gray-800 rounded-full h-3">
              <div
                className={`${color} h-3 rounded-full transition-all duration-700`}
                style={{ width: `${prob * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {recommended_bet && (
        <div className="bg-gray-800 rounded-lg p-3 mb-4">
          <span className="text-xs text-text-secondary">推薦投注：</span>
          <span className="ml-2 text-sm font-bold text-primary">{recommended_bet}</span>
        </div>
      )}

      <div className="border-t border-gray-800 pt-4">
        <h3 className="text-sm font-semibold text-text-primary mb-2">LLM 深度分析</h3>
        <p className="text-sm text-text-secondary leading-relaxed">{llm_analysis}</p>
      </div>
    </div>
  )
}
