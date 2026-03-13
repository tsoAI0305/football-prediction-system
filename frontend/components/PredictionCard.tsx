import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Prediction } from '@/lib/api';
import { Trophy, TrendingUp, Activity, Target, Brain, ChevronDown, ChevronUp } from 'lucide-react';

interface PredictionCardProps {
  prediction: Prediction;
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  const router = useRouter();
  const { date, time, league, home_team, away_team, prediction: pred, ai_analysis } = prediction;
  const [showAIAnalysis, setShowAIAnalysis] = useState(false);

  const getBorderClass = () => {
    if (pred.prediction === 'home_win') return 'from-green-400 to-emerald-500';
    if (pred.prediction === 'away_win') return 'from-red-400 to-rose-500';
    return 'from-yellow-400 to-orange-500';
  };

  const getPredictionText = () => {
    if (pred.prediction === 'home_win') return `🏠 ${home_team} 主場獲勝`;
    if (pred.prediction === 'away_win') return `✈️ ${away_team} 客場獲勝`;
    return '🤝 平局';
  };

  const getConfidenceColor = () => {
    if (pred.confidence >= 70) return 'text-green-400';
    if (pred.confidence >= 50) return 'text-yellow-300';
    return 'text-orange-300';
  };

  const handleTeamClick = (teamName: string) => {
    router.push(`/team/${encodeURIComponent(teamName)}`);
  };

  return (
    <motion.div 
      className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden border-2 border-white/50"
      whileHover={{ scale: 1.01, y: -3 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className={`h-2 bg-gradient-to-r ${getBorderClass()}`} />

      <div className="p-8">
        {/* 比賽資訊 */}
        <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
          <motion.span 
            className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-full text-sm font-bold shadow-lg flex items-center gap-2"
            whileHover={{ scale: 1.05 }}
          >
            ⏰ {date} {time}
          </motion.span>
          <motion.span 
            className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-full text-sm font-bold shadow-lg flex items-center gap-2"
            whileHover={{ scale: 1.05 }}
          >
            <Trophy className="w-4 h-4" />
            {league}
          </motion.span>
        </div>

        {/* 球隊對陣 - 可點擊 */}
        <motion.div className="text-center mb-8 bg-gradient-to-r from-gray-50 to-gray-100 py-6 rounded-2xl">
          <div className="flex items-center justify-center gap-4 md:gap-8 flex-wrap">
            <motion.button
              onClick={() => handleTeamClick(home_team)}
              className="text-2xl md:text-3xl font-black text-gray-800 hover:text-blue-600 transition-colors cursor-pointer"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              {home_team}
            </motion.button>
            <span className="text-xl md:text-2xl text-gray-400 font-bold">VS</span>
            <motion.button
              onClick={() => handleTeamClick(away_team)}
              className="text-2xl md:text-3xl font-black text-gray-800 hover:text-purple-600 transition-colors cursor-pointer"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              {away_team}
            </motion.button>
          </div>
        </motion.div>

        {/* 預測結果 */}
        <motion.div 
          className={`bg-gradient-to-r ${getBorderClass()} text-white rounded-2xl p-8 mb-6 shadow-xl`}
          whileHover={{ scale: 1.02 }}
        >
          <motion.div 
            className="text-2xl md:text-3xl font-black text-center mb-4 flex items-center justify-center gap-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Target className="w-8 h-8" />
            {getPredictionText()}
          </motion.div>
          
          <div className="text-center mb-6">
            <span className="text-lg font-semibold text-white/90">信心度</span>
            <motion.div 
              className={`text-5xl font-black ${getConfidenceColor()} mt-2`}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200 }}
            >
              {pred.confidence}%
            </motion.div>
          </div>

          {/* 機率分布 */}
          <div className="grid grid-cols-3 gap-4 bg-white/20 backdrop-blur-sm rounded-xl p-6">
            {[
              { label: '🏠 主勝', value: pred.probabilities.home_win },
              { label: '🤝 和局', value: pred.probabilities.draw },
              { label: '✈️ 客勝', value: pred.probabilities.away_win },
            ].map((prob, idx) => (
              <motion.div 
                key={idx}
                className="text-center"
                whileHover={{ scale: 1.1 }}
              >
                <motion.div 
                  className="text-3xl md:text-4xl font-black text-white mb-2"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  {prob.value}%
                </motion.div>
                <div className="text-sm font-bold text-white/90">{prob.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* 預測比分 */}
        <motion.div 
          className="text-center bg-gradient-to-r from-blue-500 to-purple-600 text-white py-6 rounded-2xl mb-6 shadow-xl"
          whileHover={{ scale: 1.05 }}
        >
          <div className="text-sm font-bold text-white/80 mb-2">預測比分</div>
          <div className="text-5xl md:text-6xl font-black">{pred.expected_score}</div>
        </motion.div>

        {/* AI 分析區塊 */}
        <motion.div className="mb-6">
          <motion.button
            onClick={() => setShowAIAnalysis(!showAIAnalysis)}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 hover:shadow-xl transition-all"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Brain className="w-6 h-6" />
            {showAIAnalysis ? ' 隱藏' : '查看'} AI 深度分析
            {showAIAnalysis ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </motion.button>

          <AnimatePresence>
            {showAIAnalysis && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200"
              >
                <div className="flex items-center gap-3 mb-4">
                  <Brain className="w-8 h-8 text-purple-600" />
                  <h3 className="text-2xl font-black text-purple-700">AI 分析報告</h3>
                </div>
                
                {ai_analysis ? (
                  <div className="prose prose-purple max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                      {ai_analysis}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-600 mb-4">此場比賽尚無 AI 深度分析</p>
                    <p className="text-sm text-gray-500">基於數據統計的預測已顯示於上方</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* 球隊統計 */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* 主隊 */}
          <motion.div 
            className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-6 border-2 border-blue-200 cursor-pointer"
            whileHover={{ scale: 1.03, borderColor: "#667eea" }}
            onClick={() => handleTeamClick(home_team)}
          >
            <h4 className="font-black text-blue-700 mb-4 text-lg flex items-center gap-2">
              <Activity className="w-5 h-5" />
              🏠 {home_team}
            </h4>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">近期狀態</span>
                <span className="font-mono font-black text-blue-600 text-base">{pred.analysis.home_form}</span>
              </div>
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">綜合實力</span>
                <span className="font-black text-blue-600 text-base">{pred.analysis.home_total_score}/100</span>
              </div>
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">主場勝率</span>
                <span className="font-bold text-gray-800">{pred.analysis.home_win_rate}%</span>
              </div>
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">場均進球</span>
                <span className="font-bold text-gray-800">{pred.analysis.home_avg_goals}</span>
              </div>
            </div>
            <div className="mt-4 text-center text-blue-600 text-sm font-bold">
              點擊查看球隊詳情 →
            </div>
          </motion.div>

          {/* 客隊 */}
          <motion.div 
            className="bg-gradient-to-br from-red-50 to-pink-50 rounded-2xl p-6 border-2 border-red-200 cursor-pointer"
            whileHover={{ scale: 1.03, borderColor: "#ef4444" }}
            onClick={() => handleTeamClick(away_team)}
          >
            <h4 className="font-black text-red-700 mb-4 text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              ✈️ {away_team}
            </h4>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">近期狀態</span>
                <span className="font-mono font-black text-red-600 text-base">{pred.analysis.away_form}</span>
              </div>
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">綜合實力</span>
                <span className="font-black text-red-600 text-base">{pred.analysis.away_total_score}/100</span>
              </div>
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">客場勝率</span>
                <span className="font-bold text-gray-800">{pred.analysis.away_win_rate}%</span>
              </div>
              <div className="flex justify-between items-center bg-white/70 px-4 py-2 rounded-lg">
                <span className="font-semibold text-gray-700">場均進球</span>
                <span className="font-bold text-gray-800">{pred.analysis.away_avg_goals}</span>
              </div>
            </div>
            <div className="mt-4 text-center text-red-600 text-sm font-bold">
              點擊查看球隊詳情 →
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
