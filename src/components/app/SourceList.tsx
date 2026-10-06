'use client';

import React, { useState } from 'react';
import { Source, PdfSource, WebSource } from '@/lib/types';
import { ChevronDown, ChevronRight, FileText, Globe, ExternalLink } from 'lucide-react';

interface SourceListProps {
  sources: Source[];
  onSelectPage?: (page: number) => void;
}

function isPdfSource(s: Source): s is PdfSource {
  return 'chunk_id' in s || 'page_start' in s;
}

function isWebSource(s: Source): s is WebSource {
  return 'url' in s;
}

export default function SourceList({ sources, onSelectPage }: SourceListProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-2.5 border-t border-black/5 dark:border-white/5 text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-mono text-[11px] font-semibold transition-colors cursor-pointer"
      >
        {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <span>
          Sources & Citations ({sources.length})
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2 animate-in fade-in slide-in-from-top-1">
          {sources.map((src, idx) => {
            if (isPdfSource(src)) {
              const page = src.page_start;
              return (
                <div
                  key={src.id || `pdf_${idx}`}
                  onClick={() => onSelectPage?.(page)}
                  className="p-2.5 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10 hover:border-emerald-500/40 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      <FileText className="w-3 h-3" />
                      [{src.id || `S${idx + 1}`}] Page {src.page_start === src.page_end ? src.page_start : `${src.page_start}-${src.page_end}`}
                    </span>
                    {typeof src.score === 'number' && (
                      <span className="text-[10px] font-mono text-slate-400">
                        score: {(src.score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed font-sans">
                    {src.snippet}
                  </p>
                </div>
              );
            }

            if (isWebSource(src)) {
              let domain = '';
              try {
                domain = new URL(src.url).hostname.replace(/^www\./, '');
              } catch {
                domain = src.url;
              }

              return (
                <div
                  key={src.id || `web_${idx}`}
                  className="p-2.5 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10 text-left"
                >
                  <div className="flex items-center justify-between mb-1">
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 font-medium text-emerald-600 dark:text-emerald-400 hover:underline line-clamp-1"
                    >
                      <Globe className="w-3 h-3 flex-shrink-0" />
                      <span>[{src.id || `W${idx + 1}`}] {src.title || domain}</span>
                      <ExternalLink className="w-2.5 h-2.5 flex-shrink-0 opacity-60" />
                    </a>
                    <span className="text-[10px] font-mono text-slate-400 ml-2 flex-shrink-0">
                      {domain}
                    </span>
                  </div>
                  {src.snippet && (
                    <p className="text-[11px] text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed font-sans">
                      {src.snippet}
                    </p>
                  )}
                </div>
              );
            }

            return null;
          })}
        </div>
      )}
    </div>
  );
}
