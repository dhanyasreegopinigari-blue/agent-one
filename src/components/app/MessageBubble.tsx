'use client';

import React from 'react';
import { ChatMessage, PdfSource } from '@/lib/types';
import MessageContent from './MessageContent';
import SourceList from './SourceList';
import ModelBadge from './ModelBadge';
import { RotateCw, AlertTriangle, User, Bot, Loader2 } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
  onRetry?: () => void;
  onSelectPage?: (page: number) => void;
}

export default function MessageBubble({
  message,
  onRetry,
  onSelectPage,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';

  const handleSelectCitation = (citeId: string) => {
    const src = message.sources?.find((s) => s.id === citeId);
    if (src && 'page_start' in src) {
      onSelectPage?.((src as PdfSource).page_start);
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 max-w-3xl ml-auto mb-4">
        <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-tr-xs px-4 py-3 bg-[#0c3822] text-white shadow-sm border border-emerald-500/30">
          <p className="text-xs sm:text-sm whitespace-pre-wrap leading-relaxed select-text">
            {message.content}
          </p>
        </div>
        <div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-3 max-w-3xl mr-auto mb-4 w-full">
      <div className="w-8 h-8 rounded-full bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 flex items-center justify-center text-slate-700 dark:text-emerald-400 flex-shrink-0 mt-0.5">
        <Bot className="w-4 h-4" />
      </div>

      <div className="flex-1 max-w-[90%] sm:max-w-[85%] rounded-2xl rounded-tl-xs px-4.5 py-3.5 bg-white/80 dark:bg-white/[0.03] backdrop-blur-md border border-black/10 dark:border-white/10 shadow-sm text-left">
        {/* Error state */}
        {message.error ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-rose-500 text-xs font-semibold">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{message.error}</span>
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-colors cursor-pointer"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Retry question</span>
              </button>
            )}
          </div>
        ) : (
          <>
            {/* Content or typing indicator */}
            {message.content ? (
              <MessageContent
                content={message.content}
                onSelectCitation={handleSelectCitation}
              />
            ) : message.pending ? (
              <div className="flex items-center gap-2 text-xs text-slate-400 font-mono py-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-500" />
                <span>Thinking...</span>
              </div>
            ) : null}

            {/* Citations and sources */}
            {message.sources && message.sources.length > 0 && (
              <SourceList
                sources={message.sources}
                onSelectPage={onSelectPage}
              />
            )}

            {/* Footer / Model info */}
            {!message.pending && (
              <div className="mt-2.5 pt-2 border-t border-black/5 dark:border-white/5 flex items-center justify-between gap-2 text-[10px] text-slate-400 select-none">
                <ModelBadge
                  modelUsed={message.model_used}
                  fallback={message.fallback}
                  grounded={message.grounded}
                />
                <span className="font-mono text-[10px]">
                  {message.created_at ? new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
