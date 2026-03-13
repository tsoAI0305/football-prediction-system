'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { predictionService, Prediction } from '@/lib/api';
import PredictionCard from '@/components/PredictionCard';
import Header from '@/components/Header';
import { Search, TrendingUp, Filter, Sparkles } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [allPredictions, setAllPredictions] = useState<Prediction[]>([]);
  const [featuredMatches, setFeaturedMatches] = useState<Prediction[]>([]);
  const [leagues, setLeagues] = useState<string[]>([]);
  const [selectedLeague, setSelectedLeague] = useState('');
  const [searchTeam, setSearchTeam] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllMatches, setShowAllMatches] = useState(false);
  const [filterType, setFilterType] = useState<'all' | 'home_win' | 'draw' | 'away_win'>('all');

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    const result = searchParams.get('result');
    
    if (result && ['home_win', 'draw', 'away_win'].includes(result)) {
      setFilterType(result as any);
      setShowAllMatches(true);
    }
  }, [searchParams]);

  useEffect(() => {
    filterPredictions();
  }, [selectedLeague, searchTeam, allPredictions, filterType]);

  const fetchInitialData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [predictionsData, leaguesData] = await Promise.all([
        predictionService.getPredictions(),
        predictionService.getLeagues(),
      ]);

      setAllPredictions(predictionsData.predictions);
      setPredictions(predictionsData.predictions);
      setLeagues(leaguesData.leagues);
      
      const hotTeams = ['Barcelona', 'Real Madrid', 'Manchester City', 'Liverpool', 'Bayern Munich', 'Arsenal', 'Chelsea', 'Paris SG', 'Inter', 'Milan'];
      const featured = predictionsData.predictions
        .filter(p => 
          p.prediction.confidence > 55 || 
          hotTeams.includes(p.home_team) || 
          hotTeams.includes(p.away_team)
        )
        .slice(0, 6);
      
      setFeaturedMatches(featured);
    } catch (err) {
      setError('無法載入預測資料，請確認後端服務是否正常運行。');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterPredictions = () => {
    let filtered = [...allPredictions];

    if (filterType !== 'all') {
      filtered = filtered.filter(p => p.prediction.prediction === filterType);
    }

    if (selectedLeague) {
      filtered = filtered.filter(p => p.league.toLowerCase() === selectedLeague.toLowerCase());
    }

    if (searchTeam) {
      const searchLower = searchTeam.toLowerCase();
      filtered = filtered.filter(
        p => p.home_team.toLowerCase().includes(searchLower) || 
             p.away_team.toLowerCase().includes(searchLower)
      );
    }

    setPredictions(filtered);
  };

  const handleStatCardClick = (type: 'all' | 'home_win' | 'draw' | 'away_win') => {
    setFilterType(type);
    setShowAllMatches(true);
    if (type === 'all') {
      router.push('/');
    } else {
      router.push(`/?result=${type}`);
    }
  };

  const displayedMatches = showAllMatches ? predictions : featuredMatches;
  const allHomeWins = allPredictions.filter(p => p.prediction.prediction === 'home_win').length;
  const allDraws = allPredictions.filter(p => p.prediction.prediction === 'draw').length;
  const allAwayWins = allPredictions.filter(p => p.prediction.prediction === 'away_win').length;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 flex items-center justify-center">
        <motion.div 
          className="text-center"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="relative w-32 h-32 mx-auto mb-8"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <div className="absolute inset-0 border-8 border-white/30 rounded-full"></div>
            <div className="absolute inset-0 border-8 border-white border-t-transparent rounded-full"></div>
          </motion.div>
          <motion.p 
            className="text-white text-2xl font-bold"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            載入 AI 預測中...
          </motion.p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 relative overflow-hidden">
      <Header />

      {/* 背景動畫效果 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-0 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl"
          animate={{ y: [0, 100, 0], x: [0, 50, 0] }}
          transition={{ duration: 20, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl"
          animate={{ y: [0, -100, 0], x: [0, -50, 0] }}
          transition={{ duration: 15, repeat: Infinity }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 relative z-10">
        {/* 標題 */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <motion.p 
            className="text-2xl text-white/90 font-semibold"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            🎯 2026年3月14-17日 賽事預測
          </motion.p>
          <motion.div
            className="mt-4 inline-flex items-center gap-2 bg-white/20 backdrop-blur-md px-6 py-3 rounded-full"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <TrendingUp className="w-5 h-5 text-white" />
            <span className="text-white font-bold">由 Groq Llama 3.3 70B 驅動</span>
          </motion.div>
        </motion.div>

        {/* 錯誤訊息 */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-8 bg-red-500/90 backdrop-blur-md border border-red-300 p-6 rounded-2xl shadow-2xl"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white">發生錯誤</h3>
                  <p className="mt-2 text-white/90">{error}</p>
                  <button
                    onClick={fetchInitialData}
                    className="mt-4 bg-white text-red-600 px-6 py-2 rounded-lg font-bold hover:bg-red-50 transition-colors"
                  >
                    重試
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 統計卡片 - 可點擊篩選 */}
        {!error && (
          <motion.div 
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            {[
              { label: '總場次', value: allPredictions.length, icon: '⚽', color: 'from-blue-500 to-blue-600', ring: 'ring-blue-400', type: 'all' as const },
              { label: '主場獲勝', value: allHomeWins, icon: '🏠', color: 'from-green-500 to-green-600', ring: 'ring-green-400', type: 'home_win' as const },
              { label: '平局', value: allDraws, icon: '🤝', color: 'from-yellow-500 to-orange-500', ring: 'ring-yellow-400', type: 'draw' as const },
              { label: '客場獲勝', value: allAwayWins, icon: '✈️', color: 'from-red-500 to-pink-600', ring: 'ring-red-400', type: 'away_win' as const },
            ].map((stat, index) => (
              <motion.button
                key={index}
                onClick={() => handleStatCardClick(stat.type)}
                className={`bg-gradient-to-br ${stat.color} rounded-2xl shadow-2xl p-6 text-center border-2 ${
                  filterType === stat.type ? 'border-white ring-4 ' + stat.ring : 'border-white/30'
                } cursor-pointer`}
                whileHover={{ scale: 1.05, rotate: 2 }}
                whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <motion.div 
                  className={`bg-white/90 w-16 h-16 md:w-20 md:h-20 rounded-full flex items-center justify-center text-4xl md:text-5xl mx-auto mb-4 ring-4 ${stat.ring}`}
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.6 }}
                >
                  {stat.icon}
                </motion.div>
                <motion.div 
                  className="text-4xl md:text-5xl font-black text-white mb-2 drop-shadow-lg"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.3 + index * 0.1, type: "spring" }}
                >
                  {stat.value}
                </motion.div>
                <div className="text-base md:text-lg text-white/95 font-bold">{stat.label}</div>
                <div className="text-xs text-white/80 mt-2">點擊篩選</div>
              </motion.button>
            ))}
          </motion.div>
        )}

        {/* 搜尋篩選區 */}
        {!error && (
          <motion.div 
            className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 mb-10 border-2 border-white/50"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
          >
            <div className="flex items-center gap-3 mb-6">
              <Search className="w-8 h-8 text-purple-600" />
              <h2 className="text-3xl font-black text-gray-800">搜尋與篩選</h2>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-3">
                  <Filter className="w-5 h-5 text-purple-600" />
                  選擇聯賽
                </label>
                <select
                  value={selectedLeague}
                  onChange={(e) => {
                    setSelectedLeague(e.target.value);
                    setShowAllMatches(true);
                  }}
                  className="w-full px-5 py-4 border-2 border-purple-200 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 transition-all font-semibold text-gray-700 bg-white"
                >
                  <option value="">🌍 所有聯賽</option>
                  {leagues.map((league) => (
                    <option key={league} value={league}>🏆 {league}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-3">
                  <Search className="w-5 h-5 text-purple-600" />
                  搜尋球隊
                </label>
                <input
                  type="text"
                  value={searchTeam}
                  onChange={(e) => {
                    setSearchTeam(e.target.value);
                    setShowAllMatches(true);
                  }}
                  placeholder="輸入球隊名稱..."
                  className="w-full px-5 py-4 border-2 border-purple-200 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 transition-all font-semibold text-gray-700"
                />
              </div>
            </div>

            {/* 搜尋結果統計 */}
            <motion.div 
              className="text-center bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 rounded-2xl"
              whileHover={{ scale: 1.02 }}
            >
              <p className="text-xl font-bold">
                {filterType !== 'all' && (
                  <span className="mr-2">
                    {filterType === 'home_win' && '🏠 主場獲勝'}
                    {filterType === 'draw' && '🤝 平局'}
                    {filterType === 'away_win' && '✈️ 客場獲勝'}
                  </span>
                )}
                {showAllMatches ? '搜尋結果：' : '🔥 熱門賽事：'}
                <span className="text-3xl font-black ml-2">{displayedMatches.length}</span> 場比賽
              </p>
            </motion.div>

            {/* 顯示全部/熱門切換 */}
            <div className="flex gap-4 justify-center mt-6">
              {!showAllMatches && (
                <button
                  onClick={() => setShowAllMatches(true)}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-2xl transition-all hover:scale-105"
                >
                  查看全部 {allPredictions.length} 場比賽 →
                </button>
              )}
              {showAllMatches && (
                <button
                  onClick={() => {
                    setShowAllMatches(false);
                    setFilterType('all');
                    setSelectedLeague('');
                    setSearchTeam('');
                    router.push('/');
                  }}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-2xl transition-all hover:scale-105"
                >
                  ← 返回熱門賽事
                </button>
              )}
            </div>
          </motion.div>
        )}

        {/* 預測列表 */}
        {!error && displayedMatches.length === 0 ? (
          <motion.div 
            className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-16 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Search className="w-24 h-24 text-gray-400 mx-auto mb-6" />
            </motion.div>
            <p className="text-2xl text-gray-600 font-bold">沒有找到符合條件的比賽</p>
            <p className="text-gray-500 mt-3 text-lg">請嘗試調整篩選條件</p>
          </motion.div>
        ) : (
          <motion.div className="space-y-8" layout>
            <AnimatePresence mode="popLayout">
              {displayedMatches.map((prediction, index) => (
                <motion.div
                  key={`${prediction.home_team}-${prediction.away_team}-${index}`}
                  initial={{ opacity: 0, y: 50, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -50, scale: 0.9 }}
                  transition={{ delay: index * 0.05, type: "spring", stiffness: 100 }}
                  layout
                >
                  <PredictionCard prediction={prediction} />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Footer */}
        {!error && (
          <motion.div 
            className="mt-16 text-center text-white/90"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
          >
            <p className="text-lg font-semibold">© 2026 AI Football Prediction System</p>
            <p className="text-sm mt-2">
              📊 數據來源: 1,289 場歷史比賽 | 🤖 AI 模型: Groq Llama 3.3 70B
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
