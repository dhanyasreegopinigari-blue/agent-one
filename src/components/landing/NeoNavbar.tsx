'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import Logo from '@/components/brand/Logo';
import {
  Sun,
  Moon,
  Menu,
  X,
  ArrowRight,
  LogOut,
} from 'lucide-react';

export default function NeoNavbar() {
  const { isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 transition-all duration-300 select-none">
      <nav
        aria-label="Main Navigation"
        className={`w-full transition-all duration-300 px-4 sm:px-6 lg:px-8 border-b ${
          isScrolled
            ? 'bg-white/90 dark:bg-[#050811]/90 backdrop-blur-2xl border-slate-200/80 dark:border-white/[0.08] shadow-md py-3'
            : 'bg-white/75 dark:bg-[#050811]/75 backdrop-blur-xl border-slate-200/50 dark:border-white/[0.05] py-4'
        }`}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-2 group transition-transform hover:scale-[1.02] shrink-0">
            <Logo size="sm" variant="auto" />
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-600 dark:text-slate-300">
            <a
              href="#how-it-works"
              className="hover:text-slate-950 dark:hover:text-white transition-colors"
            >
              How It Works
            </a>
            <a
              href="#why-agent-one"
              className="hover:text-slate-950 dark:hover:text-white transition-colors"
            >
              Why Agent One
            </a>
            <Link
              href="/dashboard"
              className="hover:text-slate-950 dark:hover:text-white transition-colors"
            >
              Web Chat
            </Link>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Theme Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
              className="w-9 h-9 rounded-full bg-slate-100 dark:bg-white/[0.06] hover:bg-slate-200 dark:hover:bg-white/[0.12] border border-slate-200 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white flex items-center justify-center transition-all cursor-pointer shrink-0 shadow-xs"
              title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-slate-700" />
              )}
            </button>

            {/* Auth Buttons */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={logout}
                  className="h-9 px-3.5 rounded-full border border-slate-200 dark:border-white/10 hover:border-rose-300 dark:hover:border-rose-500/30 bg-slate-100/80 dark:bg-white/[0.06] hover:bg-rose-50 dark:hover:bg-rose-950/30 text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 text-xs font-semibold inline-flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Sign out</span>
                </button>
                <Link
                  href="/dashboard"
                  className="h-9 px-5 rounded-full bg-emerald-500 hover:bg-emerald-400 dark:bg-[#00FF85] dark:hover:bg-[#00f57e] text-white dark:text-[#050811] text-xs font-bold inline-flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/20 transition-all cursor-pointer"
                >
                  <span>Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5 stroke-[2.5]" />
                </Link>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="hidden sm:inline-flex text-xs font-bold text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white px-3 py-1.5 transition-colors cursor-pointer"
                >
                  Sign in
                </Link>
                <Link
                  href="/signup"
                  className="h-9 px-5 rounded-full bg-emerald-500 hover:bg-emerald-400 dark:bg-[#00FF85] dark:hover:bg-[#00f57e] text-white dark:text-[#050811] text-xs font-bold inline-flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/20 transition-all cursor-pointer"
                >
                  <span>Get Started</span>
                  <ArrowRight className="w-3.5 h-3.5 stroke-[2.5]" />
                </Link>
              </div>
            )}

            {/* Mobile Hamburger Button */}
            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden w-9 h-9 rounded-full bg-slate-100 dark:bg-white/[0.06] hover:bg-slate-200 dark:hover:bg-white/[0.12] border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white flex items-center justify-center cursor-pointer shrink-0"
              aria-label="Toggle mobile menu"
            >
              {isMobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden mt-4 p-5 rounded-3xl bg-white/98 dark:bg-[#070b14]/98 backdrop-blur-2xl border border-slate-200 dark:border-white/10 shadow-2xl space-y-4 animate-in fade-in slide-in-from-top-4 duration-200 text-left">
            <div className="flex flex-col gap-2 pb-3 border-b border-slate-200/80 dark:border-white/10">
              <a
                href="#how-it-works"
                onClick={() => setIsMobileMenuOpen(false)}
                className="py-2 px-3 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 text-sm font-semibold text-slate-800 dark:text-slate-200"
              >
                How It Works
              </a>
              <a
                href="#why-agent-one"
                onClick={() => setIsMobileMenuOpen(false)}
                className="py-2 px-3 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 text-sm font-semibold text-slate-800 dark:text-slate-200"
              >
                Why Agent One
              </a>
              <Link
                href="/dashboard"
                onClick={() => setIsMobileMenuOpen(false)}
                className="py-2 px-3 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 text-sm font-semibold text-slate-800 dark:text-slate-200"
              >
                Web Chat
              </Link>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              {isAuthenticated ? (
                <Link
                  href="/dashboard"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="w-full py-3 rounded-full bg-emerald-500 text-white dark:text-black font-bold text-center text-xs"
                >
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="w-full py-2.5 rounded-full border border-slate-300 dark:border-white/20 text-slate-800 dark:text-white font-semibold text-xs text-center hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/signup"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="w-full py-3 rounded-full bg-emerald-500 text-white dark:text-black font-bold text-center text-xs shadow-lg"
                  >
                    Get started free
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
