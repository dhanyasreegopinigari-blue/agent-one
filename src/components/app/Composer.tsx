'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square } from 'lucide-react';

interface ComposerProps {
  onSend: (text: string) => void;
  onStop?: () => void;
  isStreaming?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

const MAX_CHARS = 4000;

export default function Composer({
  onSend,
  onStop,
  isStreaming = false,
  disabled = false,
  placeholder = 'Ask a question...',
}: ComposerProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (disabled || isStreaming || !text.trim()) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value.slice(0, MAX_CHARS);
    setText(val);

    // Auto-grow
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto p-2 sm:p-4">
      <div
        className={`relative flex items-end gap-2 p-2 sm:p-3 rounded-2xl bg-white/90 dark:bg-[#0c120f]/90 backdrop-blur-xl border transition-all ${
          disabled
            ? 'border-black/5 dark:border-white/5 opacity-60 bg-black/5 dark:bg-white/[0.02]'
            : 'border-black/10 dark:border-emerald-500/20 focus-within:border-emerald-500/60 focus-within:ring-1 focus-within:ring-emerald-500/20'
        }`}
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || isStreaming}
          rows={1}
          placeholder={placeholder}
          className="flex-1 max-h-48 resize-none bg-transparent py-1.5 px-2 text-xs sm:text-sm text-[#0F172A] dark:text-white placeholder:text-slate-400 dark:placeholder:text-[#8E9690] focus:outline-none leading-relaxed"
        />

        <div className="flex items-center gap-2 flex-shrink-0">
          {text.length > 3000 && (
            <span className="text-[10px] font-mono text-slate-400">
              {text.length}/{MAX_CHARS}
            </span>
          )}

          {isStreaming ? (
            <button
              onClick={onStop}
              className="w-8 h-8 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 flex items-center justify-center transition-all cursor-pointer"
              title="Stop generating"
              aria-label="Stop generating"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={disabled || !text.trim()}
              className="w-8 h-8 rounded-xl bg-[#0c3822] hover:bg-[#14532d] disabled:opacity-40 disabled:hover:bg-[#0c3822] text-white flex items-center justify-center transition-all border border-emerald-500/40 cursor-pointer disabled:cursor-not-allowed shadow-xs"
              title="Send message"
              aria-label="Send message"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
