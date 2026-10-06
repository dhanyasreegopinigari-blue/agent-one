'use client';

import React, { useState } from 'react';
import { SessionSummary } from '@/lib/types';
import Logo from '@/components/brand/Logo';
import {
  Plus,
  FileText,
  Globe,
  Trash2,
  Edit2,
  Check,
  X,
  Search,
} from 'lucide-react';

interface SessionSidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onOpenNewChat: () => void;
  onRenameSession: (id: string, newTitle: string) => Promise<any>;
  onDeleteSession: (id: string) => Promise<any>;
  className?: string;
}

function formatRelativeTime(dateStr: string): string {
  try {
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return new Date(dateStr).toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onOpenNewChat,
  onRenameSession,
  onDeleteSession,
  className = '',
}: SessionSidebarProps) {
  const [filterQuery, setFilterQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const startEditing = (s: SessionSummary, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(s.id);
    setEditTitle(s.title);
  };

  const commitEdit = async (id: string, e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      await onRenameSession(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const cancelEdit = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const confirmDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await onDeleteSession(id);
    setDeletingId(null);
  };

  return (
    <aside
      className={`w-72 sm:w-80 h-full flex flex-col bg-white/70 dark:bg-[#070b09]/90 backdrop-blur-xl border-r border-black/10 dark:border-white/10 select-none ${className}`}
    >
      {/* Brand header */}
      <div className="p-4 border-b border-black/10 dark:border-white/10 flex items-center justify-between">
        <Logo size="sm" />
      </div>

      {/* Action / New Chat button */}
      <div className="p-3">
        <button
          onClick={onOpenNewChat}
          className="w-full py-2.5 px-3.5 rounded-2xl bg-[#0c3822] hover:bg-[#14532d] text-white border border-emerald-500/40 text-xs sm:text-sm font-bold flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Search filter */}
      {sessions.length > 5 && (
        <div className="px-3 pb-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full pl-8 pr-2.5 py-1.5 text-xs bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-xl placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>
      )}

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1">
        {filteredSessions.length === 0 ? (
          <div className="p-6 text-center text-slate-400 font-mono text-xs">
            {sessions.length === 0 ? 'No chats yet' : 'No matching chats'}
          </div>
        ) : (
          filteredSessions.map((s) => {
            const isActive = s.id === activeSessionId;
            const isEditing = s.id === editingId;
            const isDeleting = s.id === deletingId;

            return (
              <div
                key={s.id}
                onClick={() => !isEditing && onSelectSession(s.id)}
                className={`group relative flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all cursor-pointer ${
                  isActive
                    ? 'bg-black/10 dark:bg-emerald-500/15 border border-black/10 dark:border-emerald-500/30 text-[#0F172A] dark:text-white'
                    : 'hover:bg-black/5 dark:hover:bg-white/5 text-slate-700 dark:text-slate-300 border border-transparent'
                }`}
              >
                {/* Type icon */}
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    s.type === 'pdf'
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                      : 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
                  }`}
                >
                  {s.type === 'pdf' ? (
                    <FileText className="w-3.5 h-3.5" />
                  ) : (
                    <Globe className="w-3.5 h-3.5" />
                  )}
                </div>

                {/* Title & relative date */}
                {isEditing ? (
                  <div
                    className="flex-1 flex items-center gap-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') commitEdit(s.id, e);
                        if (e.key === 'Escape') cancelEdit(e);
                      }}
                      autoFocus
                      className="flex-1 px-1.5 py-0.5 text-xs bg-white dark:bg-black/40 border border-emerald-500 rounded text-slate-900 dark:text-white focus:outline-none"
                    />
                    <button
                      onClick={(e) => commitEdit(s.id, e)}
                      className="p-1 text-emerald-500 hover:text-emerald-600 cursor-pointer"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="p-1 text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : isDeleting ? (
                  <div
                    className="flex-1 flex items-center justify-between text-xs text-rose-500 animate-in fade-in"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <span className="font-semibold text-[11px]">Delete chat?</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => confirmDelete(s.id, e)}
                        className="px-2 py-0.5 rounded bg-rose-500 text-white text-[10px] font-bold cursor-pointer"
                      >
                        Yes
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeletingId(null);
                        }}
                        className="px-1.5 py-0.5 rounded text-slate-400 hover:text-white text-[10px] cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium truncate">
                        {s.title || (s.type === 'pdf' ? 'PDF Chat' : 'Web Chat')}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {formatRelativeTime(s.updated_at)}
                      </div>
                    </div>

                    {/* Action buttons (hover) */}
                    <div className="hidden group-hover:flex items-center gap-1">
                      <button
                        onClick={(e) => startEditing(s, e)}
                        className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-white cursor-pointer"
                        title="Rename"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeletingId(s.id);
                        }}
                        className="p-1 rounded text-slate-400 hover:text-rose-500 cursor-pointer"
                        title="Delete"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
