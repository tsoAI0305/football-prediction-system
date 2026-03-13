'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import axios from 'axios';
import Header from '@/components/Header';
import PredictionCard from '@/components/PredictionCard';
import { ArrowLeft, TrendingUp, Activity, Target, Award } from 'lucide-react';

interface Prediction {
  date: string;
  time: string;
  league: string;
  home_team: string;
  away_team: string;
  prediction: any;
  ai_analysis?: string;
}

interface TeamDetails {
  team_name: string;
  league: string;
  recent_form: string;
  total_score: number;
  home_win_rate: number;
  away_win_rate: number;
  home_score: number;
  away_score: number;
  avg_goals: number;
  overall_ranking: number;
  total_teams: number;
  upcoming_matches: number;
}

export default function TeamPage() {
  const params = useParams();
  const router = useRouter();
  const teamName = decodeURIComponent(params.name as string);

  const [teamDetails, setTeamDetails] = useState<TeamDetails | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTeamData();
  }, [teamName]);

  const fetchTeamData = async () => {
    setLoading(true);
    try {
      const [detailsRes, predictionsRes] = await Promise.all([
        axios.get(`http://localhost:8000/api/teams/${teamName}`),
        axios.get(`http://localhost:8000/api/predictions/?team=${teamName}`),
      ]);

      setTeamDetails(detailsRes.data);
      setPredictions(predictionsRes.data.predictions);
    } catch (error) {
      console.error('Error fetching team data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500">
        <Header />
        <div className="flex items-center justify-center min-h-[80vh]">
          <motion.div
            className="text-white text-2xl font-bold"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            載入球隊資料中...
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500">
      <Header />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* 返回按鈕 */}
        <motion.button
          onClick={() => router.back()}
          className="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white px-6 py-3 rounded-xl font-bold mb-8 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <ArrowLeft className="w-5 h-5" />
          返回
        </motion.button>

        {/* 球隊標題 */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-5xl md:text-6xl font-black text-white mb-4">
            {teamName}
          </h1>
          {teamDetails && (
            <div className="flex flex-col items-center gap-2">
              <p className="text-2xl text-white/90 font-semibold">
                🏆 {teamDetails.league}
              </p>
              <p className="text-xl text-white/80">
                📊 綜合實力排名: {teamDetails.overall_ranking}/{teamDetails.total_teams}
              </p>
            </div>
          )}
        </motion.div>

        {/* 球隊統計卡片 */}
        {teamDetails && (
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* 近期狀態 */}
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 text-center shadow-lg">
              <Activity className="w-12 h-12 text-blue-600 mx-auto mb-3" />
              <div className="text-4xl font-black text-gray-800 mb-2">
                {teamDetails.recent_form}
              </div>
              <div className="text-gray-600 font-semibold">近期狀態</div>
              <div className="text-xs text-gray-400 mt-1">最近 6 場</div>
            </div>

            {/* 主場勝率 */}
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 text-center shadow-lg">
              <TrendingUp className="w-12 h-12 text-green-600 mx-auto mb-3" />
              <div className="text-4xl font-black text-gray-800 mb-2">
                {teamDetails.home_win_rate}%
              </div>
              <div className="text-gray-600 font-semibold">主場勝率</div>
              <div className="text-xs text-gray-400 mt-1">
                歷史主場數據
              </div>
            </div>

            {/* 客場勝率 */}
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 text-center shadow-lg">
              <Target className="w-12 h-12 text-purple-600 mx-auto mb-3" />
              <div className="text-4xl font-black text-gray-800 mb-2">
                {teamDetails.away_win_rate}%
              </div>
              <div className="text-gray-600 font-semibold">客場勝率</div>
              <div className="text-xs text-gray-400 mt-1">
                歷史客場數據
              </div>
            </div>

            {/* 綜合實力排名 */}
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 text-center shadow-lg">
              <Award className="w-12 h-12 text-yellow-600 mx-auto mb-3" />
              <div className="text-4xl font-black text-gray-800 mb-2">
                {teamDetails.overall_ranking}
              </div>
              <div className="text-gray-600 font-semibold">綜合實力排名</div>
              <div className="text-xs text-gray-400 mt-2 space-y-1">
                <div>(基於綜合實力分數)</div>
                <div className="flex justify-between px-2 text-sm mt-2">
                  <span>🏠 主場:</span>
                  <span className="font-bold text-green-600">
                    {teamDetails.home_score?.toFixed(1)} 分
                  </span>
                </div>
                <div className="flex justify-between px-2 text-sm">
                  <span>✈️ 客場:</span>
                  <span className="font-bold text-purple-600">
                    {teamDetails.away_score?.toFixed(1)} 分
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* 額外統計資訊 */}
        {teamDetails && (
          <motion.div
            className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-12 shadow-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-2xl font-black text-gray-800 mb-4">
              📈 詳細數據
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4">
                <div className="text-sm text-gray-600 mb-1">場均進球</div>
                <div className="text-3xl font-black text-blue-600">
                  {teamDetails.avg_goals}
                </div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4">
                <div className="text-sm text-gray-600 mb-1">即將比賽</div>
                <div className="text-3xl font-black text-green-600">
                  {teamDetails.upcoming_matches}
                </div>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4">
                <div className="text-sm text-gray-600 mb-1">綜合分數</div>
                <div className="text-3xl font-black text-purple-600">
                  {teamDetails.total_score.toFixed(1)}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* 相關比賽 */}
        <div>
          <h2 className="text-4xl font-black text-white mb-8 flex items-center gap-3">
            <span className="bg-white/20 backdrop-blur-xl rounded-2xl px-6 py-3">
              📅 即將進行的賽事
            </span>
            <span className="bg-white/20 backdrop-blur-xl rounded-2xl px-4 py-3 text-2xl">
              {predictions.length} 場
            </span>
          </h2>
          
          {predictions.length > 0 ? (
            <div className="space-y-6">
              {predictions.map((prediction, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <PredictionCard prediction={prediction} />
                </motion.div>
              ))}
            </div>
          ) : (
            <motion.div
              className="bg-white/95 backdrop-blur-xl rounded-2xl p-12 text-center shadow-lg"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <p className="text-2xl text-gray-600 font-semibold">
                暫無即將進行的比賽
              </p>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}