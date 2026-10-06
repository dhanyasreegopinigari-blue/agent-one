'use client';

import React from 'react';
import { DocumentInfo } from '@/lib/types';
import { Loader2, AlertCircle, RefreshCw, FileText, CheckCircle2 } from 'lucide-react';

interface IngestionProgressProps {
  document: DocumentInfo;
  onRetry?: () => void;
}

const STAGE_LABELS: Record<string, string> = {
  parsing: 'Reading PDF…',
  cleaning: 'Cleaning document text…',
  chunking: 'Splitting into sections…',
  embedding: 'Creating embeddings…',
  indexing: 'Building search index…',
  done: 'Document ready',
};

export default function IngestionProgress({
  document,
  onRetry,
}: IngestionProgressProps) {
  const isFailed = document.status === 'failed';
  const isReady = document.status === 'ready';

  const humanStage =
    STAGE_LABELS[document.stage] ||
    document.stage ||
    'Processing document…';

  return (
    <div className="w-full max-w-md mx-auto p-6 rounded-3xl bg-white/90 dark:bg-[#0c120f]/90 backdrop-blur-xl border border-black/10 dark:border-white/10 shadow-lg text-center select-none my-auto">
      {isFailed ? (
        <div className="space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 mx-auto flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-[#0F172A] dark:text-white mb-1">
              Ingestion Failed
            </h3>
            <p className="text-xs text-rose-600 dark:text-rose-400 leading-relaxed max-w-xs mx-auto">
              {document.error_message ||
                document.error_code ||
                'Could not process this PDF document.'}
            </p>
          </div>
          {onRetry && (
            <div className="pt-2">
              <button
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-[#0c3822] hover:bg-[#14532d] text-white border border-emerald-500/40 shadow-xs transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Upload a different PDF</span>
              </button>
            </div>
          )}
        </div>
      ) : isReady ? (
        <div className="space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 mx-auto flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-[#0F172A] dark:text-white mb-1">
              {document.filename} is ready
            </h3>
            <p className="text-xs text-slate-500 font-mono">
              {document.page_count ?? 0} pages · {document.n_chunks ?? 0} chunks indexed
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 mx-auto flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <div>
            <div className="flex items-center justify-center gap-1.5 text-xs font-mono text-slate-500 mb-1">
              <FileText className="w-3.5 h-3.5" />
              <span className="truncate max-w-[200px]">{document.filename}</span>
            </div>
            <h3 className="text-sm sm:text-base font-bold text-[#0F172A] dark:text-white mb-1">
              {humanStage}
            </h3>
            <p className="text-xs text-slate-500 font-mono">
              {document.progress}% completed
            </p>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all duration-500 rounded-full"
              style={{ width: `${Math.max(document.progress, 5)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
