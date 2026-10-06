'use client';

import React, { useState } from 'react';
import { SessionType, SessionSummary } from '@/lib/types';
import { FileText, Globe, X, ArrowRight, Loader2 } from 'lucide-react';

interface NewChatDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateSession: (type: SessionType) => Promise<SessionSummary>;
  onSessionCreated: (session: SessionSummary) => void;
}

export default function NewChatDialog({
  isOpen,
  onClose,
  onCreateSession,
  onSessionCreated,
}: NewChatDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedType, setSelectedType] = useState<SessionType | null>(null);

  if (!isOpen) return null;

  const handleSelect = async (type: SessionType) => {
    setIsSubmitting(true);
    setSelectedType(type);
    try {
      const created = await onCreateSession(type);
      onSessionCreated(created);
      onClose();
    } catch (err) {
      console.error('Failed to create session:', err);
    } finally {
      setIsSubmitting(false);
      setSelectedType(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm select-none animate-in fade-in">
      <div className="relative w-full max-w-lg rounded-3xl p-6 sm:p-8 bg-white/95 dark:bg-[#0c120f]/95 backdrop-blur-2xl border border-black/10 dark:border-emerald-500/20 shadow-2xl text-left">
        {/* Close button */}
        <button
          onClick={onClose}
          disabled={isSubmitting}
          className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
          title="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="mb-6">
          <h2 className="text-xl sm:text-2xl font-serif font-bold text-[#0F172A] dark:text-white tracking-tight">
            New Chat Session
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Choose how you would like Agent One to assist you.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* PDF Chat Card */}
          <button
            onClick={() => handleSelect('pdf')}
            disabled={isSubmitting}
            className={`p-5 rounded-2xl border text-left transition-all cursor-pointer group flex flex-col justify-between ${
              selectedType === 'pdf'
                ? 'border-emerald-500 bg-emerald-500/10'
                : 'border-black/10 dark:border-white/10 hover:border-emerald-500/50 hover:bg-black/[0.02] dark:hover:bg-white/[0.03]'
            }`}
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-[#0F172A] dark:text-white mb-1">
                PDF Chat
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Ask questions about one PDF. Answers come only from the document with page citations.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-black/5 dark:border-white/5 flex items-center justify-between text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <span>{isSubmitting && selectedType === 'pdf' ? 'Creating…' : 'Start PDF chat'}</span>
              {isSubmitting && selectedType === 'pdf' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              )}
            </div>
          </button>

          {/* Web Chat Card */}
          <button
            onClick={() => handleSelect('web')}
            disabled={isSubmitting}
            className={`p-5 rounded-2xl border text-left transition-all cursor-pointer group flex flex-col justify-between ${
              selectedType === 'web'
                ? 'border-emerald-500 bg-emerald-500/10'
                : 'border-black/10 dark:border-white/10 hover:border-emerald-500/50 hover:bg-black/[0.02] dark:hover:bg-white/[0.03]'
            }`}
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-[#0F172A] dark:text-white mb-1">
                Web Chat
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Search the internet. No PDF involved. Live citations with source links.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-black/5 dark:border-white/5 flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400">
              <span>{isSubmitting && selectedType === 'web' ? 'Creating…' : 'Start Web chat'}</span>
              {isSubmitting && selectedType === 'web' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              )}
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
