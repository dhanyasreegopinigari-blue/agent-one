'use client';

import React from 'react';
import Link from 'next/link';
import Logo from '@/components/brand/Logo';

export default function NeoFooter() {
  return (
    <footer className="bg-slate-50 dark:bg-[#03050a] border-t border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white select-none relative overflow-hidden transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-20 relative z-10 text-left">
        {/* Top 4-Column Grid */}
        <div className="grid grid-cols-1 xs:grid-cols-2 md:grid-cols-4 gap-8 lg:gap-10 pb-14 border-b border-slate-200 dark:border-white/[0.08]">
          {/* Col 1: Brand Info */}
          <div className="col-span-1 xs:col-span-2 md:col-span-1 space-y-4">
            <Link href="/" className="inline-block">
              <Logo size="sm" variant="auto" />
            </Link>

            <p className="text-xs text-slate-500 dark:text-slate-400 font-sans leading-relaxed">
              Private, local-first AI document chat grounded strictly in your PDFs with verifiable page citations.
            </p>

            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-[#00FF85] text-[11px] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-[#00FF85] animate-ping" />
              <span>Ollama & FAISS Powered</span>
            </div>
          </div>

          {/* Col 2: Pipeline */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white">
              Architecture
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li>
                <a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  PDF Parser & Chunker
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  Ollama Embeddings
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  FAISS Vector Store
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  Score Gating & Refusal
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  Page Citations
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Features */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white">
              Features
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li>
                <Link href="/dashboard" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  PDF Grounded Chat
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  Isolated Web Chat
                </Link>
              </li>
              <li>
                <a href="#why-agent-one" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  Gemini Fallback
                </a>
              </li>
              <li>
                <a href="#why-agent-one" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                  Split-Screen PDF Viewer
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4: Trust & Privacy */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white">
              Privacy & Trust
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <li>
                <span className="text-slate-800 dark:text-slate-300 font-semibold block">
                  Local-First Inference
                </span>
                <span className="text-[10px] text-slate-500 block">
                  Runs on Ollama; data stays on your machine
                </span>
              </li>
              <li>
                <span className="text-slate-800 dark:text-slate-300 font-semibold block mt-2">
                  Strict Isolation
                </span>
                <span className="text-[10px] text-slate-500 block">
                  PDF and Web chats never mix
                </span>
              </li>
              <li>
                <span className="text-slate-800 dark:text-slate-300 font-semibold block mt-2">
                  Supabase Auth
                </span>
                <span className="text-[10px] text-slate-500 block">
                  Secure JWT bearer tokens
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar: Copyright & Attribution */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-500 text-center sm:text-left">
          <p>
            © {new Date().getFullYear()} Agent One. All rights reserved.
          </p>

          <div className="flex flex-wrap items-center justify-center sm:justify-end gap-4 xs:gap-6">
            <Link href="/login" className="hover:text-slate-900 dark:hover:text-slate-300 transition-colors">
              Sign In
            </Link>
            <Link href="/signup" className="hover:text-slate-900 dark:hover:text-slate-300 transition-colors">
              Sign Up
            </Link>
            <Link href="/dashboard" className="hover:text-slate-900 dark:hover:text-slate-300 transition-colors">
              Workspace
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
