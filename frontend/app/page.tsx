'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { predictionService, Prediction } from '@/lib/api';
import PredictionCard from '@/components/PredictionCard';
import Header from '@/components/Header';
import { Search, TrendingUp, Filter } from 'lucide-react';

type ResultFilter = 'all' | 'H' | 'D' | 'A' | 'OVER';

function HomeContent() {
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
  const [filterType, setFilterType] = useState<ResultFilter>('all');

  useEffect(() => { fetchInitialData(); }, []);

  useEffect(() => {
    const result = searchParams.get('result');
    if (result && ['H', 'D', 'A', 'OVER'].includes(result)) {
      setFilterType(result as ResultFilter);
      setShowAllMatches(true);
    }
  }, [searchParams]);

  useEffect(() => { filterPredictions(); }, [selectedLeague, searchTeam, allPredictions, filterType]);

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

      // 熱門賽事：信心 > 60% 或知名球隊
      const hotTeams = ['Barcelona', 'Real Madrid', 'Manchester City', 'Liverpool',
        'Bayern München', 'Arsenal', 'Chelsea', 'Paris Saint-Germain', 'Inter Milan', 'Milan'];
      const featured = predictionsData.predictions
        .filter(p => p.prediction.confidence > 0.60 ||
          hotTeams.includes(p.home_team) || hotTeams.includes(p.away_team))
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
    if (filterType === 'OVER') {
      filtered = filtered.filter(p => p.prediction.ou_pick === 'OVER');
    } else if (filterType !== 'all') {
      filtered = filtered.filter(p => p.prediction.prediction === filterType);
    }
    if (selectedLeague) {
      filtered = filtered.filter(p => p.league.toLowerCase() === selectedLeague.toLowerCase());
    }
    if (searchTeam) {
      const s = searchTeam.toLowerCase();
      filtered = filtered.filter(p =>
        p.home_team.toLowerCase().includes(s) || p.away_team.toLowerCase().includes(s)
      );
    }
    setPredictions(filtered);
  };

  const handleStatCardClick = (type: ResultFilter) => {
    setFilterType(type);
    setShowAllMatches(true);
    router.push(type === 'all' ? '/' : `/?result=${type}`, { scroll: false });
  };

  const displayedMatches = showAllMatches ? predictions : featuredMatches;
  const allH = allPredictions.filter(p => p.prediction.prediction === 'H').length;
  const allD = allPredictions.filter(p => p.prediction.prediction === 'D').length;
  const allA = allPredictions.filter(p => p.prediction.prediction === 'A').length;
  const allOver = allPredictions.filter(p => p.prediction.ou_pick === 'OVER').length;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 flex items-center justify-center">
        <motion.div className="text-center"
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}>
          <motion.div className="relative w-32 h-32 mx-auto mb-8"
            animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }}>
            <div className="absolute inset-0 border-8 border-white/30 rounded-full" />
            <div className="absolute inset-0 border-8 border-white border-t-transparent rounded-full" />
          </motion.div>
          <motion.p className="text-white text-2xl font-bold"
            animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }}>
            載入 AI 預測中...
          </motion.p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 relative overflow-hidden">
      <Header />

      {/* 背景動畫 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div className="absolute top-0 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl"
          animate={{ y: [0, 100, 0], x: [0, 50, 0] }} transition={{ duration: 20, repeat: Infinity }} />
        <motion.div className="absolute bottom-0 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl"
          animate={{ y: [0, -100, 0], x: [0, -50, 0] }} transition={{ duration: 15, repeat: Infinity }} />
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 relative z-10">

        {/* 標題 */}
        <motion.div className="text-center mb-12"
          initial={{ opacity: 0, y: -50 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <motion.p className="text-2xl text-white/90 font-semibold"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            🎯 五大聯賽 AI 賽事預測
          </motion.p>
          <motion.div
            className="mt-4 inline-flex items-center gap-2 bg-white/20 backdrop-blur-md px-6 py-3 rounded-full"
            initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.5 }}>
            <TrendingUp className="w-5 h-5 text-white" />
            <span className="text-white font-bold">ML Ensemble + 大小球雙模型</span>
          </motion.div>
        </motion.div>

        {/* 錯誤訊息 */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="mb-8 bg-red-500/90 backdrop-blur-md border border-red-300 p-6 rounded-2xl shadow-2xl">
              <p className="text-white font-bold text-xl mb-2">發生錯誤</p>
              <p className="text-white/90">{error}</p>
              <button onClick={fetchInitialData}
                className="mt-4 bg-white text-red-600 px-6 py-2 rounded-lg font-bold hover:bg-red-50 transition-colors">
                重試
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 統計卡片（5張，加入大球統計）*/}
        {!error && (
          <motion.div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            {[
              { label: '總場次',   value: allPredictions.length, icon: '⚽', color: 'from-blue-500 to-blue-600',   ring: 'ring-blue-400',   type: 'all' as ResultFilter },
              { label: '主勝',     value: allH,                  icon: '🏠', color: 'from-green-500 to-green-600', ring: 'ring-green-400',  type: 'H'   as ResultFilter },
              { label: '平局',     value: allD,                  icon: '🤝', color: 'from-yellow-500 to-orange-500',ring: 'ring-yellow-400', type: 'D'   as ResultFilter },
              { label: '客勝',     value: allA,                  icon: '✈️', color: 'from-red-500 to-pink-600',    ring: 'ring-red-400',    type: 'A'   as ResultFilter },
              { label: '大球預測', value: allOver,               icon: '🎯', color: 'from-indigo-500 to-purple-600',ring: 'ring-indigo-400', type: 'OVER' as ResultFilter },
            ].map((stat, i) => (
              <motion.button key={i} onClick={() => handleStatCardClick(stat.type)}
                className={`bg-gradient-to-br ${stat.color} rounded-2xl shadow-2xl p-4 text-center border-2 ${
                  filterType === stat.type && stat.type !== 'all'
                    ? 'border-white ring-4 ' + stat.ring : 'border-white/30'
                } cursor-pointer`}
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 300 }}>
                <div className="text-3xl mb-2">{stat.icon}</div>
                <div className="text-3xl md:text-4xl font-black text-white mb-1">{stat.value}</div>
                <div className="text-sm text-white/90 font-bold">{stat.label}</div>
              </motion.button>
            ))}
          </motion.div>
        )}

        {/* 搜尋篩選 */}
        {!error && (
          <motion.div
            className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 mb-10 border-2 border-white/50"
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4 }}>
            <div className="flex items-center gap-3 mb-6">
              <Search className="w-8 h-8 text-purple-600" />
              <h2 className="text-3xl font-black text-gray-800">搜尋與篩選</h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-3">
                  <Filter className="w-5 h-5 text-purple-600" />選擇聯賽
                </label>
                <select value={selectedLeague}
                  onChange={e => { setSelectedLeague(e.target.value); setShowAllMatches(true); }}
                  className="w-full px-5 py-4 border-2 border-purple-200 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 font-semibold text-gray-700 bg-white">
                  <option value="">🌍 所有聯賽</option>
                  {leagues.map(l => <option key={l} value={l}>🏆 {l}</option>)}
                </select>
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-3">
                  <Search className="w-5 h-5 text-purple-600" />搜尋球隊
                </label>
                <input type="text" value={searchTeam}
                  onChange={e => { setSearchTeam(e.target.value); setShowAllMatches(true); }}
                  placeholder="輸入球隊名稱..."
                  className="w-full px-5 py-4 border-2 border-purple-200 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 font-semibold text-gray-700" />
              </div>
            </div>

            <div className="text-center bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 rounded-2xl mb-4">
              <p className="text-xl font-bold">
                {showAllMatches ? '搜尋結果：' : '🔥 熱門賽事：'}
                <span className="text-3xl font-black ml-2">{displayedMatches.length}</span> 場比賽
              </p>
            </div>

            <div className="flex gap-4 justify-center">
              {!showAllMatches ? (
                <button onClick={() => setShowAllMatches(true)}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-2xl transition-all hover:scale-105">
                  查看全部 {allPredictions.length} 場比賽 →
                </button>
              ) : (
                <button onClick={() => { setShowAllMatches(false); setFilterType('all'); setSelectedLeague(''); setSearchTeam(''); router.push('/'); }}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-2xl transition-all hover:scale-105">
                  ← 返回熱門賽事
                </button>
              )}
            </div>
          </motion.div>
        )}

        {/* 預測列表 */}
        {!error && (
          displayedMatches.length === 0 ? (
            <motion.div className="bg-white/95 rounded-3xl shadow-2xl p-16 text-center"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Search className="w-24 h-24 text-gray-400 mx-auto mb-6" />
              <p className="text-2xl text-gray-600 font-bold">沒有找到符合條件的比賽</p>
            </motion.div>
          ) : (
            <motion.div className="space-y-8" layout>
              <AnimatePresence mode="popLayout">
                {displayedMatches.map((prediction, index) => (
                  <motion.div
                    key={`${prediction.match_id}-${index}`}
                    initial={{ opacity: 0, y: 50, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -50, scale: 0.9 }}
                    transition={{ delay: index * 0.05, type: "spring", stiffness: 100 }}
                    layout>
                    <PredictionCard prediction={prediction} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )
        )}

        {/* Footer */}
        {!error && (
          <motion.div className="mt-16 text-center text-white/90"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}>
            <p className="text-lg font-semibold">© 2026 AI Football Prediction System</p>
            <p className="text-sm mt-2">📊 ML Ensemble Model | ⚽ Over/Under 2.5 | 五大聯賽即時爬蟲數據</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 flex items-center justify-center">
        <div className="text-white text-2xl font-bold">載入 AI 預測中...</div>
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
