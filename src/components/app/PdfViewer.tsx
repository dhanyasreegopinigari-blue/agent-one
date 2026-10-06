'use client';

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, FileText, Loader2, AlertCircle } from 'lucide-react';

interface PdfViewerProps {
  blobUrl: string | null;
  currentPage?: number;
  totalPages?: number | null;
  isLoading?: boolean;
  error?: string | null;
  onPageChange?: (page: number) => void;
}

export default function PdfViewer({
  blobUrl,
  currentPage = 1,
  totalPages = null,
  isLoading = false,
  error = null,
  onPageChange,
}: PdfViewerProps) {
  const [pageInput, setPageInput] = useState<string>(String(currentPage));

  useEffect(() => {
    setPageInput(String(currentPage));
  }, [currentPage]);

  const handlePageCommit = () => {
    const p = parseInt(pageInput, 10);
    if (!isNaN(p) && p >= 1) {
      const max = totalPages ? totalPages : 9999;
      const clamped = Math.min(Math.max(1, p), max);
      setPageInput(String(clamped));
      onPageChange?.(clamped);
    } else {
      setPageInput(String(currentPage));
    }
  };

  const handlePrev = () => {
    if (currentPage > 1) {
      onPageChange?.(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (!totalPages || currentPage < totalPages) {
      onPageChange?.(currentPage + 1);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center p-8 bg-black/5 dark:bg-[#070b09] rounded-2xl border border-black/10 dark:border-white/10 text-slate-500 font-mono text-xs">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500 mb-3" />
        <span>Loading PDF document...</span>
      </div>
    );
  }

  if (error || !blobUrl) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center p-8 bg-black/5 dark:bg-[#070b09] rounded-2xl border border-black/10 dark:border-white/10 text-slate-500 font-mono text-xs text-center">
        {error ? (
          <>
            <AlertCircle className="w-8 h-8 text-rose-500 mb-2" />
            <span className="text-rose-400 font-semibold mb-1">Failed to load preview</span>
            <span className="text-slate-400 max-w-xs">{error}</span>
          </>
        ) : (
          <>
            <FileText className="w-8 h-8 text-slate-400 mb-2" />
            <span>No document loaded</span>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col rounded-2xl overflow-hidden border border-black/10 dark:border-white/10 bg-slate-900 shadow-lg">
      {/* Viewer toolbar */}
      <div className="h-11 px-4 flex items-center justify-between bg-white/95 dark:bg-[#0c120f] border-b border-black/10 dark:border-white/10 select-none">
        <div className="flex items-center gap-2 text-xs font-mono font-medium text-slate-700 dark:text-slate-300">
          <FileText className="w-4 h-4 text-emerald-500" />
          <span>Document Preview</span>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-mono">
          <button
            onClick={handlePrev}
            disabled={currentPage <= 1}
            className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 disabled:opacity-40 disabled:hover:bg-transparent transition-colors cursor-pointer"
            title="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1">
            <span className="text-slate-400 text-[11px]">p.</span>
            <input
              type="text"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              onBlur={handlePageCommit}
              onKeyDown={(e) => e.key === 'Enter' && handlePageCommit()}
              className="w-10 px-1.5 py-0.5 text-center text-xs font-mono bg-black/5 dark:bg-white/5 border border-black/15 dark:border-white/15 rounded-md text-[#0F172A] dark:text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            {totalPages && (
              <span className="text-slate-400 text-[11px]">/ {totalPages}</span>
            )}
          </div>

          <button
            onClick={handleNext}
            disabled={Boolean(totalPages && currentPage >= totalPages)}
            className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 disabled:opacity-40 disabled:hover:bg-transparent transition-colors cursor-pointer"
            title="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Frame */}
      <div className="flex-1 w-full bg-slate-950 relative">
        <iframe
          src={`${blobUrl}#page=${currentPage}`}
          key={`${blobUrl}-${currentPage}`}
          title="PDF Document"
          className="w-full h-full border-0"
        />
      </div>
    </div>
  );
}
