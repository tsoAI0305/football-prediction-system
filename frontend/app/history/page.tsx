'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { getHistory, HistoryRecord, HistoryResponse } from '@/lib/api';
import Header from '@/components/Header';
import {
  Trophy, Minus, Plane,
  CheckCircle, XCircle, Clock, BarChart2, Target, Zap,
} from 'lucide-react';

// ── constants ──────────────────────────────────────────────────────────────

const RESULT_LABEL: Record<string, string> = { H: '主勝', D: '平局', A: '客勝' };
const RESULT_ICON: Record<string, typeof Trophy> = { H: Trophy, D: Minus, A: Plane };

const LEAGUE_EMOJI: Record<string, string> = {
  'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'La Liga': '🇪🇸',
  'Bundesliga': '🇩🇪',
  'Serie A': '🇮🇹',
  'Ligue 1': '🇫🇷',
};

const RESULT_GRADIENT: Record<string, string> = {
  H: 'from-emerald-500 to-green-600',
  D: 'from-amber-400 to-orange-500',
  A: 'from-rose-500 to-pink-600',
};

type ViewFilter = 'all' | 'hit' | 'miss' | 'pending' | 'over';

// ── sub-components ─────────────────────────────────────────────────────────

function StatCard({
  icon, label, value, sub, color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <div className={`bg-gradient-to-br ${color} rounded-2xl p-5 text-white shadow-xl`}>
      <div className="flex items-center gap-2 mb-3 opacity-80">{icon}<span className="text-sm font-bold uppercase tracking-wide">{label}</span></div>
      <div className="text-4xl font-black">{value}</div>
      {sub && <div className="text-sm mt-1 opacity-75">{sub}</div>}
    </div>
  );
}

function HitBadge({ isCorrect }: { isCorrect: boolean | null }) {
  if (isCorrect === null) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 text-gray-500 text-xs font-black">
        <Clock className="w-3.5 h-3.5" /> 待確認
      </span>
    );
  }
  if (isCorrect) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-black">
        <CheckCircle className="w-3.5 h-3.5" /> 命中
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-100 text-rose-700 text-xs font-black">
      <XCircle className="w-3.5 h-3.5" /> 爆冷
    </span>
  );
}

function OUBadge({ ouHit, predicted }: { ouHit: boolean | null; predicted: 'OVER' | 'UNDER' | null }) {
  const label = predicted === 'OVER' ? '大球' : predicted === 'UNDER' ? '小球' : '—';
  if (ouHit === null) return <span className="text-xs text-gray-400">{label} · 待確認</span>;
  const color = ouHit ? 'text-emerald-600' : 'text-rose-500';
  const icon = ouHit ? <CheckCircle className="w-3 h-3 inline mr-0.5" /> : <XCircle className="w-3 h-3 inline mr-0.5" />;
  return <span className={`text-xs font-semibold ${color}`}>{icon}{label} · {ouHit ? '命中' : '未中'}</span>;
}

function HistoryCard({ record, index }: { record: HistoryRecord; index: number }) {
  const gradientKey = record.predicted_result ?? 'D';
  const gradient = RESULT_GRADIENT[gradientKey];
  const PredIcon = record.predicted_result ? RESULT_ICON[record.predicted_result] : Minus;
  const ActualIcon = record.actual_result ? RESULT_ICON[record.actual_result] : Clock;

  const hasActual = record.actual_result !== null;
  const confPct = record.confidence != null ? Math.round(record.confidence * 100) : null;

  return (
    <motion.div
      className="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, type: 'spring', stiffness: 120 }}
      layout
    >
      {/* header bar */}
      <div className={`bg-gradient-to-r ${gradient} px-5 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <span>{LEAGUE_EMOJI[record.league ?? ''] ?? '🏆'}</span>
          <span className="text-white font-bold text-sm">{record.league}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-white/80 text-sm">{record.date} {record.time}</span>
          <HitBadge isCorrect={record.is_correct} />
        </div>
      </div>

      <div className="p-5">
        {/* teams */}
        <div className="flex items-center justify-between mb-4">
          <Link
            href={`/team/${encodeURIComponent(record.home_team ?? '')}`}
            className="flex-1 text-center font-black text-gray-800 text-lg hover:text-blue-600 transition-colors"
          >
            {record.home_team}
            <p className="text-xs text-gray-400 font-normal mt-0.5">主場</p>
          </Link>
          <div className="px-4">
            {hasActual ? (
              <span className="text-2xl font-black text-gray-700">
                {record.actual_home_score} – {record.actual_away_score}
              </span>
            ) : (
              <span className="text-2xl font-black text-gray-300">VS</span>
            )}
          </div>
          <Link
            href={`/team/${encodeURIComponent(record.away_team ?? '')}`}
            className="flex-1 text-center font-black text-gray-800 text-lg hover:text-purple-600 transition-colors"
          >
            {record.away_team}
            <p className="text-xs text-gray-400 font-normal mt-0.5">客場</p>
          </Link>
        </div>

        {/* prediction vs actual */}
        <div className="grid grid-cols-2 gap-3">
          {/* AI 預測 */}
          <div className="bg-indigo-50 rounded-2xl p-4">
            <p className="text-xs font-bold text-indigo-400 uppercase tracking-wide mb-2">AI 預測</p>
            <div className="flex items-center gap-2 mb-1">
              <PredIcon className="w-4 h-4 text-indigo-600" />
              <span className="text-base font-black text-indigo-700">
                {record.predicted_result ? RESULT_LABEL[record.predicted_result] : '—'}
              </span>
              {confPct !== null && (
                <span className="text-xs text-indigo-400 font-semibold">({confPct}%)</span>
              )}
            </div>
            <OUBadge ouHit={record.ou_hit} predicted={record.predicted_ou} />
          </div>

          {/* 實際結果 */}
          <div className={`rounded-2xl p-4 ${hasActual ? (record.is_correct ? 'bg-emerald-50' : 'bg-rose-50') : 'bg-gray-50'}`}>
            <p className={`text-xs font-bold uppercase tracking-wide mb-2 ${hasActual ? (record.is_correct ? 'text-emerald-500' : 'text-rose-400') : 'text-gray-400'}`}>
              實際結果
            </p>
            {hasActual ? (
              <>
                <div className="flex items-center gap-2 mb-1">
                  <ActualIcon className={`w-4 h-4 ${record.is_correct ? 'text-emerald-600' : 'text-rose-500'}`} />
                  <span className={`text-base font-black ${record.is_correct ? 'text-emerald-700' : 'text-rose-600'}`}>
                    {RESULT_LABEL[record.actual_result!]}
                  </span>
                </div>
                <span className="text-xs text-gray-500 font-semibold">
                  {record.actual_home_score} – {record.actual_away_score}（
                  {(record.actual_home_score! + record.actual_away_score!) > 2.5 ? '大球' : '小球'} ·{' '}
                  {record.actual_home_score! + record.actual_away_score!} 球）
                </span>
              </>
            ) : (
              <div className="flex items-center gap-2 text-gray-400">
                <Clock className="w-4 h-4" />
                <span className="text-sm font-semibold">尚未進行</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ── main page ──────────────────────────────────────────────────────────────

function HistoryContent() {
  const searchParams = useSearchParams();

  // Derive initial filter from URL params synchronously to avoid flash
  const initFilter = (): ViewFilter => {
    if (searchParams.get('result') === 'OU') return 'over';
    return 'all';
  };

  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<ViewFilter>(initFilter);

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getHistory({ limit: 100 });
      setData(res);
    } catch {
      setError('無法載入歷史記錄，請確認後端服務是否正常運行。');
    } finally {
      setLoading(false);
    }
  };

  const allOver = (data?.records ?? []).filter(r => r.predicted_ou === 'OVER').length;

  const filtered = (data?.records ?? []).filter(r => {
    if (filter === 'hit') return r.is_correct === true;
    if (filter === 'miss') return r.is_correct === false;
    if (filter === 'pending') return r.actual_result === null;
    if (filter === 'over') return r.predicted_ou === 'OVER';
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 flex items-center justify-center">
        <motion.div className="text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <motion.div
            className="relative w-24 h-24 mx-auto mb-6"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <div className="absolute inset-0 border-8 border-white/30 rounded-full" />
            <div className="absolute inset-0 border-8 border-white border-t-transparent rounded-full" />
          </motion.div>
          <motion.p
            className="text-white text-xl font-bold"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            載入預測歷史...
          </motion.p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 relative overflow-hidden">
      <Header />

      {/* bg blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-0 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl"
          animate={{ y: [0, 80, 0], x: [0, 40, 0] }}
          transition={{ duration: 20, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl"
          animate={{ y: [0, -80, 0], x: [0, -40, 0] }}
          transition={{ duration: 15, repeat: Infinity }}
        />
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8 relative z-10">

        {/* title */}
        <motion.div
          className="text-center mb-10"
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl md:text-5xl font-black text-white mb-2">📋 預測歷史紀錄</h1>
          <p className="text-white/75 font-semibold">預測 vs 實際結果對比 · 命中率追蹤</p>
        </motion.div>

        {/* error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="mb-8 bg-red-500/90 backdrop-blur-md border border-red-300 p-6 rounded-2xl shadow-2xl"
            >
              <p className="text-white font-bold text-lg mb-2">發生錯誤</p>
              <p className="text-white/90 text-sm">{error}</p>
              <button
                onClick={fetchHistory}
                className="mt-4 bg-white text-red-600 px-5 py-2 rounded-lg font-bold hover:bg-red-50 transition-colors text-sm"
              >
                重試
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* stats cards */}
        {data && !error && (
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          >
            <StatCard
              icon={<BarChart2 className="w-4 h-4" />}
              label="總預測場次"
              value={data.total}
              sub={`已完賽 ${data.completed} 場`}
              color="from-blue-500 to-blue-700"
            />
            <StatCard
              icon={<Target className="w-4 h-4" />}
              label="勝負命中率"
              value={data.completed > 0 ? `${data.accuracy}%` : '—'}
              sub={data.completed > 0 ? `${data.correct} / ${data.completed} 場` : '尚無完賽資料'}
              color={data.accuracy >= 60 ? 'from-emerald-500 to-green-700' : 'from-amber-500 to-orange-600'}
            />
            <StatCard
              icon={<Zap className="w-4 h-4" />}
              label="大小球命中率"
              value={data.completed > 0 ? `${data.ou_accuracy}%` : '—'}
              sub={data.completed > 0 ? `${data.ou_correct} / ${data.completed} 場` : '尚無完賽資料'}
              color="from-purple-500 to-indigo-700"
            />
            <StatCard
              icon={<CheckCircle className="w-4 h-4" />}
              label="命中場次"
              value={data.correct}
              sub={`爆冷 ${data.completed - data.correct} 場`}
              color="from-pink-500 to-rose-600"
            />
          </motion.div>
        )}

        {/* filter tabs */}
        {data && !error && (
          <motion.div
            className="flex gap-2 mb-6 bg-white/15 backdrop-blur-md rounded-2xl p-2"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          >
            {([
              { key: 'all',     label: `全部 (${data.total})`,                   icon: <BarChart2 className="w-4 h-4" /> },
              { key: 'hit',     label: `命中 (${data.correct})`,                 icon: <CheckCircle className="w-4 h-4" /> },
              { key: 'miss',    label: `爆冷 (${data.completed - data.correct})`,icon: <XCircle className="w-4 h-4" /> },
              { key: 'pending', label: `待確認 (${data.total - data.completed})`,icon: <Clock className="w-4 h-4" /> },
              { key: 'over',    label: `大球預測 (${allOver})`,                  icon: <Zap className="w-4 h-4" /> },
            ] as const).map(({ key, label, icon }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl text-sm font-bold transition-all ${
                  filter === key
                    ? 'bg-white text-gray-800 shadow-md'
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                {icon}
                <span className="hidden sm:inline">{label}</span>
                <span className="sm:hidden">{label.split(' ')[0]}</span>
              </button>
            ))}
          </motion.div>
        )}

        {/* record list */}
        {data && !error && (
          filtered.length === 0 ? (
            <motion.div
              className="bg-white/95 rounded-3xl shadow-2xl p-16 text-center"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            >
              <p className="text-2xl text-gray-500 font-bold">沒有符合條件的紀錄</p>
            </motion.div>
          ) : (
            <motion.div className="space-y-5" layout>
              <AnimatePresence mode="popLayout">
                {filtered.map((record, i) => (
                  <HistoryCard key={`${record.id}-${record.match_id}`} record={record} index={i} />
                ))}
              </AnimatePresence>
            </motion.div>
          )
        )}

        {/* footer */}
        {!error && (
          <motion.div
            className="mt-14 text-center text-white/70"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
          >
            <p className="text-sm">© 2026 AI Football Prediction System · 歷史預測準確度追蹤</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function HistoryPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 flex items-center justify-center">
        <div className="text-white text-xl font-bold">載入中...</div>
      </div>
    }>
      <HistoryContent />
    </Suspense>
  );
}
