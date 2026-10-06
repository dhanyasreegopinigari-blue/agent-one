'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { ArrowRight, ShieldCheck, Cpu, FileText, CheckCircle2 } from 'lucide-react';

const ROTATING_WORDS = ['PRIVATE', 'GROUNDED', 'LOCAL-FIRST', 'VERIFIABLE'];

export default function NeoHero() {
  const { isAuthenticated } = useAuth();
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [fadeState, setFadeState] = useState<'in' | 'out'>('in');

  useEffect(() => {
    const interval = setInterval(() => {
      setFadeState('out');
      setTimeout(() => {
        setCurrentWordIndex((prev) => (prev + 1) % ROTATING_WORDS.length);
        setFadeState('in');
      }, 300);
    }, 3200);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center pt-28 sm:pt-36 pb-16 px-4 sm:px-6 lg:px-8 overflow-hidden bg-white dark:bg-[#050811] text-slate-900 dark:text-white select-none transition-colors duration-300">
      {/* Cosmos Background Gradients & Glows */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-tr from-emerald-500/10 via-cyan-500/10 to-transparent dark:from-cyan-500/10 dark:via-emerald-500/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-gradient-to-br from-blue-500/10 via-teal-500/5 to-transparent dark:from-blue-600/10 dark:via-purple-600/10 rounded-full blur-[130px] pointer-events-none" />

      {/* Grid Backdrop */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#00000008_1px,transparent_1px),linear-gradient(to_bottom,#00000008_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="relative max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-6 items-center">
        {/* Left Column: Headlines & Pitch */}
        <div className="lg:col-span-6 xl:col-span-6 text-left space-y-6 z-10">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100/90 dark:bg-white/[0.06] border border-slate-200 dark:border-white/10 backdrop-blur-xl text-xs font-mono text-slate-700 dark:text-slate-300 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-[#00FF85] animate-ping" />
            <span className="font-semibold text-slate-900 dark:text-white">Grounded RAG Architecture</span>
            <span className="text-slate-400 dark:text-white/30">•</span>
            <span className="text-emerald-600 dark:text-[#00FF85] font-semibold">Ollama + FAISS</span>
          </div>

          {/* Monumental Headline */}
          <h1 className="text-3xl xs:text-4xl sm:text-5xl lg:text-6xl xl:text-[64px] font-sans font-black tracking-tight leading-[1.08] text-slate-950 dark:text-white break-words">
            Chat with your PDF. <br />
            Answers that are <br />
            <span
              className={`inline-block transition-all duration-300 font-mono tracking-normal text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 via-teal-600 to-blue-600 dark:from-[#00FF85] dark:via-[#00D2FF] dark:to-[#3B82F6] ${
                fadeState === 'in'
                  ? 'opacity-100 transform translate-y-0'
                  : 'opacity-0 transform -translate-y-2'
              }`}
            >
              {ROTATING_WORDS[currentWordIndex]}.
            </span>
          </h1>

          {/* Subheading */}
          <div className="space-y-3 max-w-xl">
            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed font-sans font-normal">
              Private, local-first AI answers grounded only in your document, with verifiable page citations. Running locally via Ollama with FAISS vector retrieval and exact cosine similarity.
            </p>
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 pt-2">
            <Link
              href={isAuthenticated ? '/dashboard' : '/login'}
              className="h-12 px-7 rounded-full bg-emerald-500 hover:bg-emerald-400 dark:bg-[#00FF85] dark:hover:bg-[#00f57e] text-white dark:text-[#050811] font-sans font-bold text-sm tracking-tight inline-flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer group"
            >
              <span>Launch Agent One</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform stroke-[2.5]" />
            </Link>

            <a
              href="#how-it-works"
              className="h-12 px-6 rounded-full bg-slate-100 dark:bg-white/[0.06] hover:bg-slate-200 dark:hover:bg-white/[0.12] border border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20 text-slate-800 dark:text-white font-sans font-semibold text-sm inline-flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer group shadow-xs"
            >
              <span>See How It Works</span>
              <ArrowRight className="w-4 h-4 text-emerald-600 dark:text-emerald-400 group-hover:translate-x-1 transition-transform" />
            </a>
          </div>

          {/* Trust Signals */}
          <div className="pt-4 flex flex-wrap items-center gap-5 text-xs font-mono text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-[#00FF85]" />
              <span>Strict Document Grounding</span>
            </div>
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-600 dark:text-[#00D2FF]" />
              <span>100% Local Inference (Ollama)</span>
            </div>
          </div>
        </div>

        {/* Right Column: Live Mockup Interface Card */}
        <div className="lg:col-span-6 xl:col-span-6 relative flex items-center justify-center">
          <div className="w-full max-w-lg rounded-3xl p-5 sm:p-6 bg-white/95 dark:bg-[#0A0E0C]/90 backdrop-blur-2xl border border-black/10 dark:border-emerald-500/20 shadow-2xl space-y-4 text-left">
            {/* Header info */}
            <div className="flex items-center justify-between pb-3 border-b border-black/5 dark:border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-bold text-[#0F172A] dark:text-white">
                    Northwind_Agreement.pdf
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono">
                    6 pages • 9 chunks indexed • Ready
                  </p>
                </div>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" />
                FAISS
              </span>
            </div>

            {/* Simulated Chat Dialogue */}
            <div className="space-y-3 text-xs">
              {/* User message */}
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-tr-xs px-3.5 py-2.5 bg-[#0c3822] text-white">
                  What is the required notice period for termination?
                </div>
              </div>

              {/* Assistant response */}
              <div className="flex justify-start">
                <div className="max-w-[90%] rounded-2xl rounded-tl-xs p-3.5 bg-black/5 dark:bg-white/[0.04] border border-black/5 dark:border-white/10 space-y-2">
                  <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
                    Either party may terminate this Agreement for convenience by providing at least <strong className="text-emerald-600 dark:text-emerald-400">45 days</strong> prior written notice to the other party [S1].
                  </p>
                  <div className="pt-2 border-t border-black/5 dark:border-white/5 flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      [S1] Page 3
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      Ollama · llama3.1:8b
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
