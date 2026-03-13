'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Home, Sparkles } from 'lucide-react';

export default function Header() {
  return (
    <motion.header
      className="bg-white/10 backdrop-blur-xl border-b border-white/20 sticky top-0 z-50 shadow-lg"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 100 }}
    >
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo - 可點擊返回首頁 */}
          <Link href="/">
            <motion.div
              className="flex items-center gap-3 cursor-pointer"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <motion.div
                className="text-4xl"
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              >
                ⚽
              </motion.div>
              <div>
                <h1 className="text-2xl font-black text-white">AI 足球預測系統</h1>
                <p className="text-sm text-white/80 font-semibold">Football AI Predictor</p>
              </div>
            </motion.div>
          </Link>

          {/* 返回首頁按鈕 */}
          <Link href="/">
            <motion.button
              className="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white px-6 py-3 rounded-xl font-bold transition-all"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Home className="w-5 h-5" />
              返回首頁
            </motion.button>
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
