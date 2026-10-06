'use client';

import React from 'react';
import { Cpu, AlertCircle, ShieldAlert } from 'lucide-react';

interface ModelBadgeProps {
  modelUsed: string | null;
  fallback?: boolean;
  grounded?: boolean | null;
  className?: string;
}

export default function ModelBadge({
  modelUsed,
  fallback = false,
  grounded,
  className = '',
}: ModelBadgeProps) {
  if (grounded === false && !modelUsed) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20 ${className}`}
        title="Refusal: the question cannot be answered from the document"
      >
        <ShieldAlert className="w-3 h-3 text-slate-400" />
        <span>Not found in PDF</span>
      </span>
    );
  }

  if (fallback) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-amber-500/15 text-amber-500 dark:text-amber-400 border border-amber-500/30 ${className}`}
        title="Generated via Gemini fallback after primary model error or timeout"
      >
        <AlertCircle className="w-3 h-3 text-amber-500" />
        <span>Gemini fallback</span>
      </span>
    );
  }

  if (modelUsed) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono text-slate-500 dark:text-slate-400 bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 ${className}`}
        title={`Generated using local Ollama model: ${modelUsed}`}
      >
        <Cpu className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
        <span>Ollama · {modelUsed}</span>
      </span>
    );
  }

  return null;
}
