'use client';

import React, { useState, useEffect, useRef } from 'react';
import { getHealth } from '@/lib/api';
import { Health } from '@/lib/types';
import { Activity, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

export default function StatusPopover() {
  const [isOpen, setIsOpen] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const data = await getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const getStatusDot = (isGood: boolean, isWarning = false) => {
    if (isGood) return 'bg-emerald-500';
    if (isWarning) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="relative" ref={popoverRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-mono font-medium text-slate-700 dark:text-slate-300 bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-white/10 border border-black/10 dark:border-white/10 transition-all cursor-pointer"
        title="System Status"
        aria-label="System status"
      >
        <Activity className="w-3.5 h-3.5 text-emerald-500" />
        <span className="hidden sm:inline">Status</span>
        <span
          className={`w-2 h-2 rounded-full ${
            health?.status === 'ok'
              ? 'bg-emerald-500'
              : health?.status === 'degraded'
              ? 'bg-amber-500'
              : 'bg-slate-400'
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-72 rounded-2xl p-4 bg-white/95 dark:bg-[#0c120f]/95 backdrop-blur-xl border border-black/10 dark:border-emerald-500/20 shadow-2xl z-50 text-left animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between pb-3 border-b border-black/10 dark:border-white/10">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#0F172A] dark:text-white uppercase tracking-wider font-mono">
                System Status
              </span>
              {health?.version && (
                <span className="text-[10px] text-slate-500 font-mono">v{health.version}</span>
              )}
            </div>
            <button
              onClick={fetchStatus}
              disabled={isLoading}
              className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors cursor-pointer"
              title="Refresh status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="py-3 space-y-2.5 text-xs">
            {/* Ollama */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${getStatusDot(
                    health?.ollama?.status === 'ok' || health?.ollama?.available === true
                  )}`}
                />
                <span className="font-medium text-slate-800 dark:text-slate-200">Ollama (Local LLM)</span>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                {health?.ollama?.status || (health?.ollama?.available ? 'online' : 'unreachable')}
              </span>
            </div>

            {/* Gemini */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${getStatusDot(
                    health?.gemini?.status === 'configured' || health?.gemini?.available === true,
                    health?.gemini?.status === 'disabled'
                  )}`}
                />
                <span className="font-medium text-slate-800 dark:text-slate-200">Gemini (Fallback)</span>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                {health?.gemini?.status || (health?.gemini?.available ? 'ready' : 'inactive')}
              </span>
            </div>

            {/* Web Search */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${getStatusDot(
                    health?.web_search?.status === 'ok' || health?.web_search?.available === true
                  )}`}
                />
                <span className="font-medium text-slate-800 dark:text-slate-200">Web Search</span>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                {health?.web_search?.provider || 'SearXNG'}
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-black/10 dark:border-white/10 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono">
            <span>Local-first architecture</span>
            <span>
              {health?.status === 'ok' ? (
                <span className="text-emerald-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> All systems online
                </span>
              ) : health ? (
                <span className="text-amber-500 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Degraded
                </span>
              ) : (
                <span className="text-rose-500 flex items-center gap-1">
                  <XCircle className="w-3 h-3" /> Backend offline
                </span>
              )}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
