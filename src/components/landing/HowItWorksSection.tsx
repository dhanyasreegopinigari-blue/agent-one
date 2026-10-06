'use client';

import React from 'react';
import { UploadCloud, MessageSquare, ShieldCheck, Globe, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function HowItWorksSection() {
  const steps = [
    {
      step: '01',
      title: 'Upload Your PDF',
      description:
        'Upload your PDF document (up to 50 MB, 500 pages). PyMuPDF parses the layout, cleans the text, and splits it into deterministic chunks.',
      icon: <UploadCloud className="w-6 h-6 text-emerald-500" />,
      detail: 'Local Ollama embeddings & FAISS index',
    },
    {
      step: '02',
      title: 'Ask Questions',
      description:
        'Ask anything in natural language. Relevant chunks are retrieved using exact cosine similarity with strict score and margin gating.',
      icon: <MessageSquare className="w-6 h-6 text-emerald-500" />,
      detail: 'Deterministic context retrieval',
    },
    {
      step: '03',
      title: 'Get Cited Answers',
      description:
        'Local Ollama synthesizes responses strictly grounded in the document text, with clickable [S#] citations pointing directly to page numbers.',
      icon: <ShieldCheck className="w-6 h-6 text-emerald-500" />,
      detail: 'Strict grounding & off-topic refusal',
    },
  ];

  return (
    <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto relative select-none">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider mb-4 border border-emerald-500/20">
          <span>Deterministic Pipeline</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-serif font-bold text-[#0F172A] dark:text-white tracking-tight">
          How Agent One Works
        </h2>
        <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
          Private, local-first AI answers grounded only in your document, with verifiable page citations.
        </p>
      </div>

      {/* 3 Step Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 mb-12">
        {steps.map((s) => (
          <div
            key={s.step}
            className="p-6 sm:p-8 rounded-3xl bg-white/70 dark:bg-white/[0.02] border border-black/10 dark:border-white/10 hover:border-emerald-500/40 transition-all flex flex-col justify-between shadow-xs"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-2xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 flex items-center justify-center">
                  {s.icon}
                </div>
                <span className="text-2xl font-mono font-bold text-slate-300 dark:text-white/20">
                  {s.step}
                </span>
              </div>
              <h3 className="text-lg font-bold text-[#0F172A] dark:text-white mb-2">
                {s.title}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
                {s.description}
              </p>
            </div>
            <div className="pt-4 border-t border-black/5 dark:border-white/5 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
              {s.detail}
            </div>
          </div>
        ))}
      </div>

      {/* Separate Web Chat Callout */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-blue-500/10 via-emerald-500/5 to-transparent border border-blue-500/20 dark:border-blue-500/20 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-500 flex items-center justify-center flex-shrink-0 mt-1">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-base font-bold text-[#0F172A] dark:text-white mb-1">
              Need to search the live web?
            </h4>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
              Start a separate Web Chat to search the internet with live links and source snippets. Web searches are strictly isolated from your private PDF sessions and never cross-pollinate.
            </p>
          </div>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-xs flex-shrink-0"
        >
          <span>Try Web Chat</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </section>
  );
}
