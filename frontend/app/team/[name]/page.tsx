'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import Header from '@/components/Header';
import PredictionCard from '@/components/PredictionCard';
import {
  getTeamDetails, getTeamMatches,
  TeamDetails, TacticalProfile, LineupByFormation,
  Prediction, Injury, TopPlayer, LineupPlayer,
} from '@/lib/api';
import {
  ArrowLeft, TrendingUp, Activity, Target, Award,
  AlertTriangle, Star, Zap, Users, Brain,
} from 'lucide-react';

// ── Form badge ──────────────────────────────────────────────────────────────

function FormBadge({ ch }: { ch: string }) {
  const cfg: Record<string, string> = {
    W: 'bg-emerald-500 text-white',
    D: 'bg-amber-400  text-white',
    L: 'bg-rose-500   text-white',
  };
  const label: Record<string, string> = { W: '勝', D: '平', L: '負' };
  const cls = cfg[ch] ?? 'bg-gray-300 text-gray-700';
  return (
    <span className={`${cls} inline-flex items-center justify-center w-9 h-9 rounded-full font-black text-sm`}>
      {label[ch] ?? ch}
    </span>
  );
}

// ── Stat type config ────────────────────────────────────────────────────────

const STAT_CFG: Record<TopPlayer['stat_type'], { label: string; icon: string; accent: string; bg: string }> = {
  rating:  { label: '最佳評分', icon: '⭐', accent: 'text-yellow-600', bg: 'from-yellow-50 to-yellow-100' },
  goals:   { label: '進球王',   icon: '⚽', accent: 'text-emerald-600', bg: 'from-emerald-50 to-emerald-100' },
  assists: { label: '助攻王',   icon: '🅰️', accent: 'text-blue-600',    bg: 'from-blue-50 to-blue-100' },
};

// ── Tactical style card ─────────────────────────────────────────────────────

function TacticalStyleCard({ profile }: { profile: TacticalProfile }) {
  return (
    <motion.div
      className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.18 }}
    >
      {/* Header */}
      <h3 className="text-xl font-black text-gray-800 mb-4 flex items-center gap-2">
        <Brain className="w-5 h-5 text-indigo-500" />
        戰術風格 DNA
        {/* Formation badge */}
        <span className="ml-auto flex items-center gap-1.5 bg-indigo-50 border border-indigo-200 text-indigo-700 text-sm font-black px-3 py-1 rounded-full">
          <span className="text-base">🏟️</span>
          {profile.formation}
        </span>
      </h3>

      {/* Style tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        {profile.style_info.map((info) => (
          <span
            key={info.key}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-black ${info.badge_class}`}
          >
            <span>{info.emoji}</span>
            <span>{info.label_zh}</span>
          </span>
        ))}
        {/* Alternate formations */}
        {profile.alternate_formations.length > 0 && (
          <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200">
            備用：{profile.alternate_formations.slice(0, 2).join(' / ')}
          </span>
        )}
      </div>

      {/* DNA description */}
      <p className="text-gray-600 text-sm leading-relaxed mb-4 italic border-l-4 border-indigo-300 pl-3">
        {profile.tactical_dna}
      </p>

      {/* Evidence bullets */}
      {profile.style_evidence.length > 0 && (
        <div>
          <p className="text-xs font-black text-gray-500 uppercase tracking-wider mb-2">數據依據</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {profile.style_evidence.map((ev, i) => {
              const parts = ev.split('→');
              return (
                <div key={i} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 text-xs">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                  <span className="text-gray-600">{parts[0]?.trim()}</span>
                  {parts[1] && (
                    <>
                      <span className="text-gray-300">→</span>
                      <span className="font-bold text-indigo-700">{parts[1]?.trim()}</span>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Metric mini-bar if DB stats available */}
      {profile.metrics.db_matches > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-100 grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { label: '場均射門',  value: profile.metrics.shots_pg,   unit: '次',  color: 'text-blue-600' },
            { label: '射正',      value: profile.metrics.sot_pg,     unit: '次',  color: 'text-emerald-600' },
            { label: '犯規',      value: profile.metrics.fouls_pg,   unit: '次',  color: 'text-orange-600' },
            { label: '角球',      value: profile.metrics.corners_pg, unit: '個',  color: 'text-purple-600' },
          ].filter(m => m.value !== null).map(({ label, value, unit, color }) => (
            <div key={label} className="text-center">
              <div className={`text-lg font-black ${color}`}>{value}{unit}</div>
              <div className="text-xs text-gray-400">{label}</div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// ── Formation board ─────────────────────────────────────────────────────────

function PlayerToken({ player }: { player: LineupPlayer }) {
  return (
    <div className="flex flex-col items-center gap-0.5 min-w-0">
      {/* shirt icon */}
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
        <span className="text-white text-xs font-black">
          {player.player_name.split(' ').pop()?.slice(0, 3).toUpperCase()}
        </span>
      </div>
      <span className="text-center text-xs font-bold text-gray-700 leading-tight max-w-[72px] truncate">
        {player.player_name.split(' ').pop()}
      </span>
      <span className="text-xs text-indigo-500 font-bold">⭐ {player.rating.toFixed(1)}</span>
    </div>
  );
}

function FormationBoard({ board }: { board: LineupByFormation }) {
  return (
    <motion.div
      className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.22 }}
    >
      <h3 className="text-xl font-black text-gray-800 mb-5 flex items-center gap-2">
        <span className="text-xl">🏟️</span>
        戰術陣型板
        <span className="ml-1 bg-indigo-100 text-indigo-600 text-sm font-black px-2.5 py-0.5 rounded-full">
          {board.formation}
        </span>
      </h3>

      {/* Pitch background */}
      <div className="relative rounded-xl overflow-hidden"
        style={{
          background: 'linear-gradient(180deg, #16a34a 0%, #15803d 45%, #15803d 55%, #16a34a 100%)',
          minHeight: '340px',
        }}
      >
        {/* Centre circle hint */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex justify-center pointer-events-none opacity-20">
          <div className="w-20 h-20 rounded-full border-2 border-white" />
        </div>
        {/* Halfway line */}
        <div className="absolute inset-x-4 top-1/2 h-px bg-white/30 pointer-events-none" />

        {/* Formation rows */}
        <div className="relative z-10 flex flex-col gap-4 py-4 px-2">
          {board.rows.map((row, ri) => (
            <div key={ri}>
              {/* Row label */}
              <div className="text-center mb-2">
                <span className="inline-block bg-black/30 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {row.label}
                </span>
              </div>
              {/* Players */}
              <div className={`flex justify-center gap-3 flex-wrap`}>
                {row.players.map((p, pi) => (
                  <div key={pi} className="flex flex-col items-center gap-0.5 min-w-0">
                    <div className="w-11 h-11 rounded-full bg-white/90 border-2 border-white shadow-lg flex items-center justify-center">
                      <span className="text-indigo-800 text-xs font-black leading-none text-center px-0.5">
                        {p.player_name.split(' ').pop()?.slice(0, 4)}
                      </span>
                    </div>
                    <span className="text-white text-xs font-bold drop-shadow text-center max-w-[68px] truncate">
                      {p.player_name.split(' ').pop()}
                    </span>
                    <span className="text-yellow-300 text-xs font-bold drop-shadow">
                      {p.rating.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-gray-400 mt-3">
        ＊AI 最佳位置佈陣，已排除傷病名單球員
      </p>
    </motion.div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function TeamPage() {
  const params   = useParams();
  const router   = useRouter();
  const teamName = decodeURIComponent(params.name as string);

  const [details,     setDetails]     = useState<TeamDetails | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);

  useEffect(() => { load(); }, [teamName]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [d, p] = await Promise.all([
        getTeamDetails(teamName),
        getTeamMatches(teamName),
      ]);
      setDetails(d);
      setPredictions(p);
    } catch {
      setError('無法載入球隊資料，請確認後端服務是否正常運行。');
    } finally {
      setLoading(false);
    }
  }

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500">
        <Header />
        <div className="flex items-center justify-center min-h-[80vh]">
          <motion.div className="text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <motion.div
              className="relative w-20 h-20 mx-auto mb-6"
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            >
              <div className="absolute inset-0 border-8 border-white/30 rounded-full" />
              <div className="absolute inset-0 border-8 border-white border-t-transparent rounded-full" />
            </motion.div>
            <p className="text-white text-xl font-bold">載入球隊資料中...</p>
          </motion.div>
        </div>
      </div>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500">
        <Header />
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <div className="bg-white/95 rounded-3xl p-12 shadow-2xl">
            <p className="text-2xl font-black text-gray-800 mb-3">找不到球隊資料</p>
            <p className="text-gray-500 mb-6">{error}</p>
            <button
              onClick={() => router.back()}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-3 rounded-xl font-bold hover:shadow-xl transition-all"
            >
              返回
            </button>
          </div>
        </div>
      </div>
    );
  }

  const d = details!;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500">
      <Header />

      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Back */}
        <motion.button
          onClick={() => router.back()}
          className="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-xl font-bold mb-8 transition-colors"
          whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
        >
          <ArrowLeft className="w-4 h-4" /> 返回
        </motion.button>

        {/* ── Team title ─────────────────────────────────────────────────── */}
        <motion.div
          className="text-center mb-10"
          initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-5xl md:text-6xl font-black text-white mb-3">{teamName}</h1>
          <p className="text-xl text-white/90 font-semibold mb-1">🏆 {d.league}</p>
          <p className="text-white/70">
            聯賽第 {d.overall_ranking} 名 · {d.points} 積分 ·&nbsp;
            {d.wins}勝 {d.draws}平 {d.losses}負（{d.played} 場）
          </p>
        </motion.div>

        {/* ── 4 stat cards ───────────────────────────────────────────────── */}
        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        >
          {/* 近期狀態 */}
          <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-5 text-center shadow-lg">
            <Activity className="w-10 h-10 text-blue-600 mx-auto mb-3" />
            <div className="flex justify-center gap-1 mb-2 flex-wrap">
              {d.recent_form
                ? d.recent_form.split('').map((ch, i) => <FormBadge key={i} ch={ch} />)
                : <span className="text-gray-400 text-sm">暫無資料</span>
              }
            </div>
            <div className="text-gray-600 font-semibold text-sm">近期狀態</div>
            <div className="text-xs text-gray-400 mt-0.5">最近 {d.recent_form.length || '—'} 場</div>
          </div>

          {/* 主場勝率 */}
          <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-5 text-center shadow-lg">
            <TrendingUp className="w-10 h-10 text-green-600 mx-auto mb-3" />
            <div className="text-4xl font-black text-gray-800 mb-1">{d.home_win_rate}%</div>
            <div className="text-gray-600 font-semibold text-sm">主場勝率</div>
            <div className="text-xs text-gray-400 mt-0.5">歷史主場數據</div>
          </div>

          {/* 客場勝率 */}
          <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-5 text-center shadow-lg">
            <Target className="w-10 h-10 text-purple-600 mx-auto mb-3" />
            <div className="text-4xl font-black text-gray-800 mb-1">{d.away_win_rate}%</div>
            <div className="text-gray-600 font-semibold text-sm">客場勝率</div>
            <div className="text-xs text-gray-400 mt-0.5">歷史客場數據</div>
          </div>

          {/* 聯賽排名 */}
          <div className="bg-white/95 backdrop-blur-xl rounded-2xl p-5 text-center shadow-lg">
            <Award className="w-10 h-10 text-yellow-500 mx-auto mb-3" />
            <div className="text-4xl font-black text-gray-800 mb-1">
              {d.overall_ranking ? d.overall_ranking : <span className="text-2xl text-gray-400">讀取中</span>}
            </div>
            <div className="text-gray-600 font-semibold text-sm">聯賽排名</div>
            <div className="text-xs text-gray-400 mt-1 space-y-0.5">
              <div className="flex justify-between px-1">
                <span>🏠 主場</span>
                <span className="font-bold text-green-600">{d.home_score.toFixed(1)}</span>
              </div>
              <div className="flex justify-between px-1">
                <span>✈️ 客場</span>
                <span className="font-bold text-purple-600">{d.away_score.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── 詳細數據 ───────────────────────────────────────────────────── */}
        <motion.div
          className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
        >
          <h3 className="text-xl font-black text-gray-800 mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-500" /> 詳細數據
          </h3>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { label: '場均進球', value: d.avg_goals,              color: 'text-blue-600',   bg: 'from-blue-50 to-blue-100' },
              { label: '進球數',   value: d.goals_for,              color: 'text-emerald-600', bg: 'from-emerald-50 to-emerald-100' },
              { label: '失球數',   value: d.goals_against,          color: 'text-rose-600',   bg: 'from-rose-50 to-rose-100' },
              { label: '進失球差', value: (d.goal_diff > 0 ? '+' : '') + d.goal_diff, color: d.goal_diff >= 0 ? 'text-emerald-600' : 'text-rose-600', bg: 'from-gray-50 to-gray-100' },
              { label: '即將比賽', value: d.upcoming_matches,       color: 'text-green-600',  bg: 'from-green-50 to-green-100' },
              { label: '綜合分數', value: d.total_score.toFixed(1), color: 'text-purple-600', bg: 'from-purple-50 to-purple-100' },
            ].map(({ label, value, color, bg }) => (
              <div key={label} className={`bg-gradient-to-br ${bg} rounded-xl p-3 text-center`}>
                <div className="text-xs text-gray-500 mb-1">{label}</div>
                <div className={`text-2xl font-black ${color}`}>{value}</div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* ── 戰術風格 DNA ──────────────────────────────────────────────── */}
        {d.tactical_profile && (
          <TacticalStyleCard profile={d.tactical_profile} />
        )}

        {/* ── 戰術陣型板 ────────────────────────────────────────────────── */}
        {d.lineup_by_formation && d.lineup_by_formation.rows.length > 0 && (
          <FormationBoard board={d.lineup_by_formation} />
        )}

        {/* ── 核心球員 ───────────────────────────────────────────────────── */}
        {d.top_players.length > 0 && (
          <motion.div
            className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.27 }}
          >
            <h3 className="text-xl font-black text-gray-800 mb-4 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" /> 核心球員
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {d.top_players.map((p, i) => {
                const cfg = STAT_CFG[p.stat_type];
                return (
                  <div key={i} className={`bg-gradient-to-br ${cfg.bg} rounded-xl p-4`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{cfg.icon}</span>
                      <span className={`text-xs font-black ${cfg.accent} uppercase tracking-wide`}>
                        {cfg.label}
                      </span>
                    </div>
                    <p className="font-black text-gray-800 text-base leading-tight mb-2">
                      {p.player_name}
                    </p>
                    <div className="flex gap-3 text-sm text-gray-600">
                      <span>⚽ {p.goals}</span>
                      <span>🅰️ {p.assists}</span>
                      <span>⭐ {p.rating.toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ── 預計最佳陣容 (fallback flat grid when no formation board) ── */}
        {!d.lineup_by_formation && d.lineup.length > 0 && (
          <motion.div
            className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.29 }}
          >
            <h3 className="text-xl font-black text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-xl">🏟️</span> 預計最佳陣容
              <span className="ml-1 bg-indigo-100 text-indigo-600 text-xs font-black px-2 py-0.5 rounded-full">
                {d.lineup.length} 人
              </span>
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              {d.lineup.map((p: LineupPlayer, i: number) => (
                <div key={i} className="bg-indigo-50 rounded-xl p-3">
                  <p className="font-black text-gray-800 text-sm leading-tight mb-1.5">
                    {p.player_name}
                  </p>
                  <div className="flex gap-2 text-xs text-gray-500">
                    <span>⚽ {p.goals}</span>
                    <span>🅰️ {p.assists}</span>
                    <span className="text-indigo-600 font-bold">⭐ {p.rating.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400">＊AI 專業位置佈陣，已排除傷病名單球員</p>
          </motion.div>
        )}

        {/* ── 重要傷員 ───────────────────────────────────────────────────── */}
        {d.injuries.length > 0 && (
          <motion.div
            className="bg-white/95 backdrop-blur-xl rounded-2xl p-6 mb-6 shadow-lg"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.31 }}
          >
            <h3 className="text-xl font-black text-gray-800 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              重要傷員
              <span className="ml-1 bg-orange-100 text-orange-600 text-xs font-black px-2 py-0.5 rounded-full">
                {d.injuries.length} 人
              </span>
            </h3>
            <div className="space-y-2">
              {d.injuries.map((inj, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between bg-orange-50 rounded-xl px-4 py-2.5"
                >
                  <div className="flex items-center gap-3">
                    <span className="bg-orange-200 text-orange-700 text-xs font-black w-8 h-8 rounded-full flex items-center justify-center">
                      {inj.position || '?'}
                    </span>
                    <div>
                      <p className="font-bold text-gray-800 text-sm">{inj.player}</p>
                      <p className="text-xs text-orange-600">{inj.info || '傷病'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">預計復出</p>
                    <p className="text-xs font-bold text-gray-700">
                      {inj.expected_return && inj.expected_return !== '-' && inj.expected_return !== 'nan'
                        ? inj.expected_return
                        : '待定'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* ── 即將進行的賽事 ─────────────────────────────────────────────── */}
        <div>
          <h2 className="text-3xl font-black text-white mb-6 flex items-center gap-3">
            <span className="bg-white/20 backdrop-blur-xl rounded-2xl px-5 py-2.5">
              📅 即將進行的賽事
            </span>
            <span className="bg-white/20 backdrop-blur-xl rounded-2xl px-4 py-2.5 text-2xl">
              {predictions.length} 場
            </span>
          </h2>

          {predictions.length > 0 ? (
            <div className="space-y-5">
              {predictions.map((prediction, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                >
                  <PredictionCard prediction={prediction} />
                </motion.div>
              ))}
            </div>
          ) : (
            <motion.div
              className="bg-white/95 backdrop-blur-xl rounded-2xl p-12 text-center shadow-lg"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            >
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-xl text-gray-500 font-semibold">暫無即將進行的比賽</p>
            </motion.div>
          )}
        </div>

      </div>
    </div>
  );
}
