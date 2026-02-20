'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <nav className="bg-surface border-b border-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-2xl">⚽</span>
            <span className="text-xl font-bold text-text-primary">Football AI Predictor</span>
          </Link>

          {/* Desktop menu */}
          <div className="hidden md:flex items-center space-x-6">
            <Link
              href="/"
              className="text-text-secondary hover:text-primary transition-colors duration-200"
            >
              首頁
            </Link>
            <Link
              href="/history"
              className="text-text-secondary hover:text-primary transition-colors duration-200"
            >
              歷史記錄
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-text-secondary hover:text-text-primary"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-800">
            <div className="flex flex-col space-y-4">
              <Link
                href="/"
                className="text-text-secondary hover:text-primary transition-colors duration-200"
                onClick={() => setIsMenuOpen(false)}
              >
                首頁
              </Link>
              <Link
                href="/history"
                className="text-text-secondary hover:text-primary transition-colors duration-200"
                onClick={() => setIsMenuOpen(false)}
              >
                歷史記錄
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
