'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useSessions } from '@/hooks/useSessions';
import { useIngestion } from '@/hooks/useIngestion';
import { usePdfBlob } from '@/hooks/usePdfBlob';
import { SessionSummary } from '@/lib/types';
import SessionSidebar from './SessionSidebar';
import NewChatDialog from './NewChatDialog';
import ChatPanel from './ChatPanel';
import PdfViewer from './PdfViewer';
import StatusPopover from './StatusPopover';
import {
  Menu,
  FileText,
  Globe,
  Sun,
  Moon,
  LogOut,
  User,
} from 'lucide-react';

export default function AppShell() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlSessionId = searchParams.get('s');

  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const {
    sessions,
    create: handleCreateSession,
    rename: handleRenameSession,
    remove: handleRemoveSession,
    updateSessionDocument,
  } = useSessions();

  const [activeSessionId, setActiveSessionId] = useState<string | null>(urlSessionId);
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);
  const [isSidebarOpenMobile, setIsSidebarOpenMobile] = useState(false);
  const [activeMobileTab, setActiveMobileTab] = useState<'chat' | 'pdf'>('chat');
  const [pdfPage, setPdfPage] = useState<number>(1);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  // Sync activeSessionId with sessions list once loaded
  useEffect(() => {
    if (urlSessionId) {
      setActiveSessionId(urlSessionId);
    } else if (sessions.length > 0 && !activeSessionId) {
      const firstId = sessions[0].id;
      setActiveSessionId(firstId);
      router.replace(`/dashboard?s=${firstId}`);
    }
  }, [urlSessionId, sessions, activeSessionId, router]);

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;

  // Ingestion hook for active session
  const { document, setDocument, retry: retryIngestion } = useIngestion(
    activeSession?.id ?? null,
    activeSession?.document ?? null,
    (updatedDoc) => {
      if (activeSession) {
        updateSessionDocument(activeSession.id, updatedDoc);
      }
    }
  );

  // PDF blob preview hook
  const isPdfReady = Boolean(activeSession?.type === 'pdf' && document?.status === 'ready');
  const { blobUrl, isLoading: pdfBlobLoading, error: pdfBlobError } = usePdfBlob(
    activeSession?.id ?? null,
    isPdfReady
  );

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
    router.replace(`/dashboard?s=${id}`);
    setIsSidebarOpenMobile(false);
    setActiveMobileTab('chat');
  };

  const handleSessionCreated = (created: SessionSummary) => {
    setActiveSessionId(created.id);
    router.replace(`/dashboard?s=${created.id}`);
    setIsSidebarOpenMobile(false);
    setActiveMobileTab('chat');
  };

  const handleDocumentUploaded = (updatedSession: SessionSummary) => {
    if (updatedSession.document) {
      setDocument(updatedSession.document);
      updateSessionDocument(updatedSession.id, updatedSession.document);
    }
  };

  const handleSelectPage = (page: number) => {
    setPdfPage(page);
    setActiveMobileTab('pdf');
  };

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-[var(--bg-canvas)] text-[var(--text-primary)] relative select-none">
      {/* Mobile sidebar overlay backdrop */}
      {isSidebarOpenMobile && (
        <div
          onClick={() => setIsSidebarOpenMobile(false)}
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs lg:hidden"
        />
      )}

      {/* Sidebar: Fixed on desktop, sliding drawer on mobile */}
      <div
        className={`fixed inset-y-0 left-0 z-50 transform lg:transform-none lg:static transition-transform duration-300 ease-in-out ${
          isSidebarOpenMobile ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <SessionSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onOpenNewChat={() => {
            setIsNewChatOpen(true);
            setIsSidebarOpenMobile(false);
          }}
          onRenameSession={handleRenameSession}
          onDeleteSession={async (id) => {
            await handleRemoveSession(id);
            if (activeSessionId === id) {
              const remaining = sessions.filter((s) => s.id !== id);
              if (remaining.length > 0) {
                handleSelectSession(remaining[0].id);
              } else {
                setActiveSessionId(null);
                router.replace('/dashboard');
              }
            }
          }}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="h-14 px-4 border-b border-black/10 dark:border-white/10 flex items-center justify-between bg-white/70 dark:bg-[#070b09]/80 backdrop-blur-md z-10 flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setIsSidebarOpenMobile(true)}
              className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 cursor-pointer"
              aria-label="Open sidebar"
            >
              <Menu className="w-4 h-4" />
            </button>

            {/* Active Session Info */}
            {activeSession ? (
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase tracking-wider ${
                    activeSession.type === 'pdf'
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                      : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                  }`}
                >
                  {activeSession.type === 'pdf' ? (
                    <FileText className="w-3 h-3" />
                  ) : (
                    <Globe className="w-3 h-3" />
                  )}
                  {activeSession.type.toUpperCase()}
                </span>
                <h1 className="text-xs sm:text-sm font-semibold truncate text-[#0F172A] dark:text-white">
                  {activeSession.title}
                </h1>
              </div>
            ) : (
              <span className="text-xs text-slate-400 font-mono">Agent One</span>
            )}
          </div>

          {/* Right header controls */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Mobile Tabs Switcher for PDF Sessions */}
            {activeSession?.type === 'pdf' && isPdfReady && (
              <div className="flex lg:hidden bg-black/5 dark:bg-white/5 p-0.5 rounded-xl border border-black/10 dark:border-white/10 text-xs font-mono">
                <button
                  onClick={() => setActiveMobileTab('chat')}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                    activeMobileTab === 'chat'
                      ? 'bg-white dark:bg-[#0c120f] shadow-xs text-emerald-600 dark:text-emerald-400 font-bold'
                      : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveMobileTab('pdf')}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                    activeMobileTab === 'pdf'
                      ? 'bg-white dark:bg-[#0c120f] shadow-xs text-emerald-600 dark:text-emerald-400 font-bold'
                      : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                  }`}
                >
                  PDF
                </button>
              </div>
            )}

            {/* System Status Popover */}
            <StatusPopover />

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-black/5 dark:hover:bg-white/5 border border-black/10 dark:border-white/10 transition-colors cursor-pointer"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <Sun className="w-3.5 h-3.5 text-amber-400" />
              ) : (
                <Moon className="w-3.5 h-3.5 text-[#1E3A2B]" />
              )}
            </button>

            {/* User Profile / Logout menu */}
            <div className="relative">
              <button
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center gap-1.5 p-1 sm:px-2 sm:py-1 rounded-xl hover:bg-black/5 dark:hover:bg-white/5 border border-black/10 dark:border-white/10 transition-colors cursor-pointer"
              >
                <div className="w-6 h-6 rounded-full bg-emerald-600/20 text-emerald-500 flex items-center justify-center text-xs font-bold">
                  {user?.name ? user.name[0].toUpperCase() : <User className="w-3.5 h-3.5" />}
                </div>
                <span className="hidden sm:inline text-xs font-medium max-w-[100px] truncate text-slate-700 dark:text-slate-200">
                  {user?.name ?? 'User'}
                </span>
              </button>

              {userDropdownOpen && (
                <div
                  onMouseLeave={() => setUserDropdownOpen(false)}
                  className="absolute right-0 top-full mt-1.5 w-48 rounded-2xl p-2 bg-white/95 dark:bg-[#0c120f]/95 backdrop-blur-xl border border-black/10 dark:border-emerald-500/20 shadow-2xl z-50 text-left animate-in fade-in"
                >
                  <div className="px-3 py-2 border-b border-black/5 dark:border-white/5">
                    <p className="text-xs font-bold truncate text-[#0F172A] dark:text-white">
                      {user?.name}
                    </p>
                    <p className="text-[10px] text-slate-500 truncate font-mono">
                      {user?.email ?? 'Anonymous Session'}
                    </p>
                  </div>
                  <button
                    onClick={async () => {
                      setUserDropdownOpen(false);
                      await logout();
                      router.replace('/login');
                    }}
                    className="w-full mt-1 px-3 py-2 rounded-xl text-xs font-semibold text-rose-500 hover:bg-rose-500/10 flex items-center gap-2 transition-colors cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* 2 or 3-Zone Workspace Body */}
        <div className="flex-1 flex overflow-hidden min-h-0 relative">
          {/* Chat Panel */}
          <div
            className={`flex-1 flex flex-col h-full min-w-0 ${
              activeSession?.type === 'pdf' && isPdfReady && activeMobileTab === 'pdf'
                ? 'hidden lg:flex'
                : 'flex'
            }`}
          >
            <ChatPanel
              session={activeSession}
              document={document}
              onUploaded={handleDocumentUploaded}
              onRetryIngestion={retryIngestion}
              onSelectPage={handleSelectPage}
            />
          </div>

          {/* PDF Viewer Zone: visible on lg+ if PDF is ready, or on mobile when activeMobileTab is 'pdf' */}
          {activeSession?.type === 'pdf' && isPdfReady && (
            <div
              className={`w-full lg:w-[48%] xl:w-[45%] h-full p-2 sm:p-3 bg-black/[0.02] dark:bg-black/20 border-l border-black/10 dark:border-white/10 ${
                activeMobileTab === 'pdf' ? 'flex' : 'hidden lg:flex'
              }`}
            >
              <PdfViewer
                blobUrl={blobUrl}
                currentPage={pdfPage}
                totalPages={document?.page_count ?? null}
                isLoading={pdfBlobLoading}
                error={pdfBlobError}
                onPageChange={(p) => setPdfPage(p)}
              />
            </div>
          )}
        </div>
      </div>

      {/* New Chat Dialog Modal */}
      <NewChatDialog
        isOpen={isNewChatOpen}
        onClose={() => setIsNewChatOpen(false)}
        onCreateSession={handleCreateSession}
        onSessionCreated={handleSessionCreated}
      />
    </div>
  );
}
