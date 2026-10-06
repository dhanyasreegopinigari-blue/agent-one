'use client';

import React from 'react';
import NeoNavbar from './NeoNavbar';
import NeoHero from './NeoHero';
import HowItWorksSection from './HowItWorksSection';
import FinalCallToAction from './FinalCallToAction';
import NeoFooter from './NeoFooter';
import { ShieldCheck, Cpu, Database, Globe } from 'lucide-react';

export default function GraphIntelligenceLanding() {
  const features = [
    {
      title: 'Local-First Inference',
      description:
        'Your PDF text is embedded and queried locally using Ollama. No document excerpts leave your infrastructure during normal operation.',
      icon: <Cpu className="w-6 h-6 text-emerald-500" />,
      badge: 'Ollama 8B',
    },
    {
      title: 'Strict Document Grounding',
      description:
        'Answers are synthesized only from retrieved document chunks with verifiable [S#] citations. Off-topic questions refuse immediately without LLM calls.',
      icon: <ShieldCheck className="w-6 h-6 text-emerald-500" />,
      badge: 'Zero Fabrication',
    },
    {
      title: 'FAISS Vector Search',
      description:
        'Each PDF gets its own dedicated FAISS IndexFlatIP index with L2-normalized embeddings, guaranteeing exact cosine similarity search.',
      icon: <Database className="w-6 h-6 text-emerald-500" />,
      badge: 'Exact Cosine',
    },
    {
      title: 'Isolated Web Search',
      description:
        'Web search operates in completely separate chat sessions. Your internal documents and public internet queries never cross-pollinate.',
      icon: <Globe className="w-6 h-6 text-emerald-500" />,
      badge: 'Strict Separation',
    },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-[#050811] text-slate-900 dark:text-white selection:bg-emerald-500/20 selection:text-emerald-900 dark:selection:text-[#00FF85] overflow-x-hidden font-sans transition-colors duration-300 antialiased">
      {/* Navbar */}
      <NeoNavbar />

      {/* Main Landing Content */}
      <main className="relative flex flex-col w-full overflow-hidden">
        {/* Hero Section */}
        <NeoHero />

        {/* How It Works Section */}
        <HowItWorksSection />

        {/* Why Agent One Features Section */}
        <section id="why-agent-one" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto select-none">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider mb-4 border border-emerald-500/20">
              <span>Core Principles</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-serif font-bold text-[#0F172A] dark:text-white tracking-tight">
              Why Choose Agent One
            </h2>
            <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
              Designed from the ground up for privacy, reliability, and precision document intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
            {features.map((f, i) => (
              <div
                key={i}
                className="p-8 rounded-3xl bg-white/70 dark:bg-white/[0.02] border border-black/10 dark:border-white/10 hover:border-emerald-500/40 transition-all shadow-xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-2xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 flex items-center justify-center">
                      {f.icon}
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[11px] font-mono font-bold border border-emerald-500/20">
                      {f.badge}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-[#0F172A] dark:text-white mb-2">
                    {f.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                    {f.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <FinalCallToAction />
      </main>

      {/* Footer */}
      <NeoFooter />
    </div>
  );
}
