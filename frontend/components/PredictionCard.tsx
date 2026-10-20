'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Prediction, resultLabel, getTeamMatches } from '@/lib/api';
import {
  Trophy, Minus, Plane, TrendingUp, TrendingDown,
  AlertCircle, ChevronDown, ChevronUp,
  Activity, Shield, Zap, Users
} from 'lucide-react';

interface Props {
  prediction: Prediction;
}

const RESULT_CONFIG = {
  H: { label: '主勝', icon: Trophy, gradient: 'from-emerald-500 to-green-600',  badge: 'bg-green-100 text-green-800' },
  D: { label: '平局', icon: Minus,  gradient: 'from-amber-400 to-orange-500',    badge: 'bg-amber-100 text-amber-800' },
  A: { label: '客勝', icon: Plane,  gradient: 'from-rose-500 to-pink-600',        badge: 'bg-rose-100 text-rose-800' },
};

const LEAGUE_EMOJI: Record<string, string> = {
  'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'La Liga': '🇪🇸',
  'Bundesliga': '🇩🇪',
  'Serie A': '🇮🇹',
  'Ligue 1': '🇫🇷',
};

interface TeamStats {
  matches: number;
  predicted_wins: number;
  predicted_draws: number;
  over_count: number;
}

function computeTeamStats(matches: Prediction[], teamName: string): TeamStats {
  const isHome = (p: Prediction) => p.home_team === teamName;
  const wins = matches.filter(p =>
    (isHome(p) && p.prediction.prediction === 'H') ||
    (!isHome(p) && p.prediction.prediction === 'A')
  ).length;
  const draws = matches.filter(p => p.prediction.prediction === 'D').length;
  const over  = matches.filter(p => p.prediction.ou_pick === 'OVER').length;
  return { matches: matches.length, predicted_wins: wins, predicted_draws: draws, over_count: over };
}

export default function PredictionCard({ prediction }: Props) {
  const p   = prediction.prediction;
  const cfg = RESULT_CONFIG[p.prediction];
  const Icon = cfg.icon;

  const confPct   = Math.round(p.confidence * 100);
  const over25Pct = Math.round(p.over25_prob * 100);
  const isOver    = p.ou_pick === 'OVER';

  // 展開狀態
  const [expanded, setExpanded]       = useState(false);
  const [activeTab, setActiveTab]     = useState<'home' | 'away' | 'odds'>('home');
  const [homeMatches, setHomeMatches] = useState<Prediction[] | null>(null);
  const [awayMatches, setAwayMatches] = useState<Prediction[] | null>(null);
  const [loadingTeam, setLoadingTeam] = useState(false);

  const confColor =
    confPct >= 70 ? 'text-emerald-600' :
    confPct >= 55 ? 'text-amber-500' : 'text-gray-400';

  const handleExpand = async () => {
    if (!expanded && homeMatches === null) {
      setLoadingTeam(true);
      try {
        const [hm, am] = await Promise.all([
          getTeamMatches(prediction.home_team),
          getTeamMatches(prediction.away_team),
        ]);
        setHomeMatches(hm);
        setAwayMatches(am);
      } catch { /* ignore */ }
      setLoadingTeam(false);
    }
    setExpanded(v => !v);
  };

  const homeStats = homeMatches ? computeTeamStats(homeMatches, prediction.home_team) : null;
  const awayStats = awayMatches ? computeTeamStats(awayMatches, prediction.away_team) : null;

  return (
    <motion.div
      className="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100 hover:shadow-2xl transition-shadow duration-300"
      layout
    >
      {/* ── 頂部色帶 ───────────────────────────────────────────────────── */}
      <div className={`bg-gradient-to-r ${cfg.gradient} px-6 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span className="text-lg">{LEAGUE_EMOJI[prediction.league] ?? '🏆'}</span>
          <span className="text-white font-bold text-sm">{prediction.league}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-white/80 text-sm">{prediction.date} {prediction.time}</span>
          <span className={`${cfg.badge} px-3 py-1 rounded-full font-black text-xs flex items-center gap-1`}>
            <Icon className="w-3 h-3" />
            {cfg.label}
          </span>
        </div>
      </div>

      <div className="p-6">
        {/* ── 球隊對陣 ─────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex-1 text-center">
            <Link
              href={`/team/${encodeURIComponent(prediction.home_team)}`}
              className="text-xl font-black text-gray-800 hover:text-blue-600 transition-colors"
            >
              {prediction.home_team}
            </Link>
            <button
              onClick={() => { handleExpand(); setActiveTab('home'); }}
              className="block w-full text-xs text-gray-400 mt-1 hover:text-blue-400 transition-colors"
            >
              主場 · 展開詳情
            </button>
          </div>
          <div className="px-4 flex flex-col items-center">
            <span className="text-2xl font-black text-gray-300">VS</span>
          </div>
          <div className="flex-1 text-center">
            <Link
              href={`/team/${encodeURIComponent(prediction.away_team)}`}
              className="text-xl font-black text-gray-800 hover:text-purple-600 transition-colors"
            >
              {prediction.away_team}
            </Link>
            <button
              onClick={() => { handleExpand(); setActiveTab('away'); }}
              className="block w-full text-xs text-gray-400 mt-1 hover:text-purple-400 transition-colors"
            >
              客場 · 展開詳情
            </button>
          </div>
        </div>

        {/* ── 機率條 ───────────────────────────────────────────────────── */}
        <div className="mb-5">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>主勝 {Math.round(p.home_win_prob * 100)}%</span>
            <span>平局 {Math.round(p.draw_prob * 100)}%</span>
            <span>客勝 {Math.round(p.away_win_prob * 100)}%</span>
          </div>
          <div className="flex rounded-full overflow-hidden h-3 bg-gray-100">
            <motion.div className="bg-emerald-500 h-full"
              initial={{ width: 0 }}
              animate={{ width: `${p.home_win_prob * 100}%` }}
              transition={{ duration: 0.8, delay: 0.1 }} />
            <motion.div className="bg-amber-400 h-full"
              initial={{ width: 0 }}
              animate={{ width: `${p.draw_prob * 100}%` }}
              transition={{ duration: 0.8, delay: 0.2 }} />
            <motion.div className="bg-rose-500 h-full"
              initial={{ width: 0 }}
              animate={{ width: `${p.away_win_prob * 100}%` }}
              transition={{ duration: 0.8, delay: 0.3 }} />
          </div>
        </div>

        {/* ── 信心度 + 大小球 ──────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gray-50 rounded-2xl p-4 text-center">
            <p className="text-xs text-gray-400 mb-1 font-semibold uppercase tracking-wide">AI 信心度</p>
            <p className={`text-3xl font-black ${confColor}`}>{confPct}%</p>
            <div className="mt-2 bg-gray-200 rounded-full h-1.5">
              <motion.div
                className={`h-1.5 rounded-full ${confPct >= 70 ? 'bg-emerald-500' : confPct >= 55 ? 'bg-amber-500' : 'bg-gray-400'}`}
                initial={{ width: 0 }}
                animate={{ width: `${confPct}%` }}
                transition={{ duration: 0.8 }} />
            </div>
          </div>
          <div className={`rounded-2xl p-4 text-center ${isOver ? 'bg-blue-50' : 'bg-purple-50'}`}>
            <p className="text-xs text-gray-400 mb-1 font-semibold uppercase tracking-wide">大小球 2.5</p>
            <div className="flex items-center justify-center gap-2">
              {isOver
                ? <TrendingUp className="w-5 h-5 text-blue-600" />
                : <TrendingDown className="w-5 h-5 text-purple-600" />}
              <p className={`text-2xl font-black ${isOver ? 'text-blue-600' : 'text-purple-600'}`}>
                {isOver ? '大球' : '小球'}
              </p>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {isOver ? `${over25Pct}%` : `${100 - over25Pct}%`} 機率
            </p>
          </div>
        </div>

        {/* ── 投注建議 ─────────────────────────────────────────────────── */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-4 flex items-start gap-3 mb-4">
          <AlertCircle className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-bold text-indigo-500 mb-1 uppercase tracking-wide">投注建議</p>
            <p className="text-sm text-gray-700 font-semibold">{p.betting_advice}</p>
          </div>
        </div>

        {/* ── 展開按鈕 ─────────────────────────────────────────────────── */}
        <button
          onClick={handleExpand}
          className="w-full flex items-center justify-center gap-2 py-2 text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          {expanded ? '收起詳情' : '展開詳情 · 球隊數據 · 賽事分析'}
        </button>
      </div>

      {/* ── 展開區塊 ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden border-t border-gray-100"
          >
            <div className="p-6 bg-gray-50">
              {/* Tab 切換 */}
              <div className="flex gap-2 mb-5">
                {([
                  { key: 'home', label: prediction.home_team, icon: Shield },
                  { key: 'away', label: prediction.away_team, icon: Plane },
                  { key: 'odds', label: '賽事分析', icon: Activity },
                ] as const).map(({ key, label, icon: TabIcon }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                      activeTab === key
                        ? 'bg-white shadow text-gray-800'
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
                  >
                    <TabIcon className="w-4 h-4" />
                    <span className="hidden md:inline">{label}</span>
                    <span className="md:hidden">{key === 'home' ? '主' : key === 'away' ? '客' : '分析'}</span>
                  </button>
                ))}
              </div>

              {loadingTeam && (
                <div className="text-center py-8 text-gray-400">
                  <motion.div className="inline-block w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full"
                    animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }} />
                  <p className="mt-2 text-sm">載入球隊數據...</p>
                </div>
              )}

              {/* 主隊詳情 */}
              {!loadingTeam && activeTab === 'home' && homeStats && (
                <TeamDetailPanel
                  teamName={prediction.home_team}
                  stats={homeStats}
                  isHome
                  matches={homeMatches ?? []}
                  league={prediction.league}
                />
              )}

              {/* 客隊詳情 */}
              {!loadingTeam && activeTab === 'away' && awayStats && (
                <TeamDetailPanel
                  teamName={prediction.away_team}
                  stats={awayStats}
                  isHome={false}
                  matches={awayMatches ?? []}
                  league={prediction.league}
                />
              )}

              {/* 賽事分析 */}
              {activeTab === 'odds' && (
                <MatchAnalysisPanel prediction={prediction} />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── 球隊詳情子元件 ─────────────────────────────────────────────────────────

function TeamDetailPanel({
  teamName, stats, isHome, matches, league,
}: {
  teamName: string;
  stats: TeamStats;
  isHome: boolean;
  matches: Prediction[];
  league: string;
}) {
  const winRate = stats.matches > 0 ? Math.round((stats.predicted_wins / stats.matches) * 100) : 0;
  const overRate = stats.matches > 0 ? Math.round((stats.over_count / stats.matches) * 100) : 0;
  const accent = isHome ? 'text-blue-600' : 'text-purple-600';
  const bg = isHome ? 'bg-blue-50' : 'bg-purple-50';
  const bar = isHome ? 'bg-blue-500' : 'bg-purple-500';

  // 最近5場（本聯賽同隊）
  const recentLeague = matches.filter(m => m.league === league).slice(0, 5);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Users className={`w-5 h-5 ${accent}`} />
        <h3 className="font-black text-gray-800">{teamName}</h3>
        <span className="text-xs text-gray-400">{isHome ? '· 主場' : '· 客場'}</span>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: '預測場次', value: stats.matches },
          { label: '預測勝場', value: stats.predicted_wins },
          { label: '大球場次', value: stats.over_count },
        ].map(({ label, value }) => (
          <div key={label} className={`${bg} rounded-xl p-3 text-center`}>
            <p className={`text-2xl font-black ${accent}`}>{value}</p>
            <p className="text-xs text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* 勝率條 */}
      <div className={`${bg} rounded-xl p-4`}>
        <div className="flex justify-between text-sm mb-2">
          <span className="font-bold text-gray-700">預測勝率</span>
          <span className={`font-black ${accent}`}>{winRate}%</span>
        </div>
        <div className="bg-white/60 rounded-full h-2.5">
          <motion.div className={`${bar} h-2.5 rounded-full`}
            initial={{ width: 0 }}
            animate={{ width: `${winRate}%` }}
            transition={{ duration: 0.6 }} />
        </div>
        <div className="flex justify-between text-sm mt-3 mb-2">
          <span className="font-bold text-gray-700">大球比例</span>
          <span className={`font-black ${accent}`}>{overRate}%</span>
        </div>
        <div className="bg-white/60 rounded-full h-2.5">
          <motion.div className={`${bar} h-2.5 rounded-full`}
            initial={{ width: 0 }}
            animate={{ width: `${overRate}%` }}
            transition={{ duration: 0.6, delay: 0.1 }} />
        </div>
      </div>

      {/* 近期賽程 */}
      {recentLeague.length > 0 && (
        <div>
          <p className="text-xs font-bold text-gray-400 mb-2 uppercase tracking-wide">近期本聯賽賽程</p>
          <div className="space-y-2">
            {recentLeague.map((m, i) => {
              const mIsHome = m.home_team === teamName;
              const pred = m.prediction.prediction;
              const win = (mIsHome && pred === 'H') || (!mIsHome && pred === 'A');
              const draw = pred === 'D';
              return (
                <div key={i} className="flex items-center justify-between bg-white rounded-xl px-4 py-2 text-sm">
                  <span className="text-gray-500 text-xs w-20">{m.date}</span>
                  <span className="font-semibold text-gray-700 flex-1 text-center">
                    {m.home_team} <span className="text-gray-300">vs</span> {m.away_team}
                  </span>
                  <span className={`text-xs font-black px-2 py-0.5 rounded-full ${
                    win ? 'bg-green-100 text-green-700' :
                    draw ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-600'
                  }`}>
                    {win ? '預勝' : draw ? '預平' : '預負'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── 賽事分析子元件 ─────────────────────────────────────────────────────────

function MatchAnalysisPanel({ prediction }: { prediction: Prediction }) {
  const p = prediction.prediction;

  const items = [
    { label: '主勝機率', value: Math.round(p.home_win_prob * 100), unit: '%', color: 'bg-emerald-500' },
    { label: '平局機率', value: Math.round(p.draw_prob * 100),     unit: '%', color: 'bg-amber-400' },
    { label: '客勝機率', value: Math.round(p.away_win_prob * 100), unit: '%', color: 'bg-rose-500' },
    { label: '大球機率', value: Math.round(p.over25_prob * 100),   unit: '%', color: 'bg-blue-500' },
    { label: '小球機率', value: Math.round(p.under25_prob * 100),  unit: '%', color: 'bg-purple-500' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Zap className="w-5 h-5 text-indigo-500" />
        <h3 className="font-black text-gray-800">完整機率分析</h3>
      </div>

      {items.map(({ label, value, unit, color }) => (
        <div key={label}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 font-semibold">{label}</span>
            <span className="font-black text-gray-800">{value}{unit}</span>
          </div>
          <div className="bg-gray-200 rounded-full h-2.5">
            <motion.div className={`${color} h-2.5 rounded-full`}
              initial={{ width: 0 }}
              animate={{ width: `${value}%` }}
              transition={{ duration: 0.6 }} />
          </div>
        </div>
      ))}

      <div className="bg-indigo-50 rounded-xl p-4 mt-4">
        <p className="text-xs font-bold text-indigo-400 mb-2 uppercase tracking-wide">AI 投注建議</p>
        <p className="text-gray-700 font-semibold text-sm">{p.betting_advice}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-center">
        <div className="bg-white rounded-xl p-3 border border-gray-100">
          <p className="text-xs text-gray-400">最強預測</p>
          <p className="text-lg font-black text-gray-800 mt-1">
            {{ H: '主勝', D: '平局', A: '客勝' }[p.prediction]}
          </p>
        </div>
        <div className="bg-white rounded-xl p-3 border border-gray-100">
          <p className="text-xs text-gray-400">大小球建議</p>
          <p className={`text-lg font-black mt-1 ${p.ou_pick === 'OVER' ? 'text-blue-600' : 'text-purple-600'}`}>
            {p.ou_pick === 'OVER' ? '大球' : '小球'}
          </p>
        </div>
      </div>
    </div>
  );
}
