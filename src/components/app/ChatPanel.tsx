'use client';

import React, { useRef, useEffect, useState } from 'react';
import { SessionSummary, DocumentInfo } from '@/lib/types';
import { useChat } from '@/hooks/useChat';
import MessageBubble from './MessageBubble';
import Composer from './Composer';
import UploadDropzone from './UploadDropzone';
import IngestionProgress from './IngestionProgress';
import { FileText, Globe, Sparkles } from 'lucide-react';

interface ChatPanelProps {
  session: SessionSummary | null;
  document: DocumentInfo | null;
  onUploaded: (updatedSession: SessionSummary) => void;
  onRetryIngestion?: () => void;
  onSelectPage?: (page: number) => void;
}

export default function ChatPanel({
  session,
  document,
  onUploaded,
  onRetryIngestion,
  onSelectPage,
}: ChatPanelProps) {
  const {
    messages,
    isStreaming,
    currentStage,
    send,
    stop,
    retryLast,
  } = useChat(session?.id ?? null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [userScrolledUp, setUserScrolledUp] = useState(false);

  // Auto-scroll logic
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 80;
    setUserScrolledUp(!isAtBottom);
  };

  useEffect(() => {
    if (!userScrolledUp && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming, currentStage, userScrolledUp]);

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500 font-mono text-xs">
        <Sparkles className="w-8 h-8 text-slate-400 mb-2" />
        <span>Select or create a chat session to get started</span>
      </div>
    );
  }

  const isPdf = session.type === 'pdf';
  const hasNoDoc = isPdf && !document;
  const isDocProcessing = isPdf && document && document.status === 'processing';
  const isDocFailed = isPdf && document && document.status === 'failed';
  const isDocReady = isPdf && document && document.status === 'ready';

  const isComposerDisabled = isPdf && !isDocReady;
  const composerPlaceholder = isPdf
    ? isDocReady
      ? 'Ask anything about this PDF...'
      : 'Upload a PDF to start chatting'
    : 'Search the web...';

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[var(--bg-canvas)] relative">
      {/* Scrollable message viewport */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 sm:px-6 py-6"
      >
        {/* PDF session initial states */}
        {hasNoDoc && (
          <div className="h-full flex items-center justify-center">
            <UploadDropzone sessionId={session.id} onUploaded={onUploaded} />
          </div>
        )}

        {(isDocProcessing || isDocFailed) && document && (
          <div className="h-full flex items-center justify-center">
            <IngestionProgress
              document={document}
              onRetry={onRetryIngestion}
            />
          </div>
        )}

        {/* Message list for Ready PDF or Web session */}
        {(!isPdf || isDocReady) && (
          <>
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 select-none max-w-md mx-auto">
                <div className="w-12 h-12 rounded-2xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3">
                  {isPdf ? <FileText className="w-6 h-6" /> : <Globe className="w-6 h-6" />}
                </div>
                <h3 className="text-base font-bold text-[#0F172A] dark:text-white mb-1.5">
                  {isPdf ? 'Document Grounded Chat' : 'Web Search Chat'}
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed max-w-xs">
                  {isPdf
                    ? `Answers will be generated strictly from ${document?.filename ?? 'the uploaded PDF'} with page citations.`
                    : 'Search questions will be answered with live web citations.'}
                </p>
              </div>
            ) : (
              <div className="space-y-4 max-w-4xl mx-auto pb-4">
                {messages.map((m) => (
                  <MessageBubble
                    key={m.id}
                    message={m}
                    onRetry={retryLast}
                    onSelectPage={onSelectPage}
                  />
                ))}

                {/* Progress banner for pipeline stages */}
                {isStreaming && currentStage && (
                  <div className="text-left max-w-3xl ml-11 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 animate-pulse">
                    {currentStage === 'retrieving'
                      ? 'Retrieving relevant document sections…'
                      : currentStage === 'searching'
                      ? 'Searching the web…'
                      : currentStage === 'generating'
                      ? 'Synthesizing response…'
                      : `${currentStage}…`}
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </>
        )}
      </div>

      {/* Composer toolbar */}
      <div className="border-t border-black/10 dark:border-white/10 bg-white/50 dark:bg-[#06080d]/80 backdrop-blur-md">
        <Composer
          onSend={send}
          onStop={stop}
          isStreaming={isStreaming}
          disabled={isComposerDisabled}
          placeholder={composerPlaceholder}
        />
      </div>
    </div>
  );
}
