'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  listSessions,
  createSession as apiCreateSession,
  renameSession as apiRenameSession,
  deleteSession as apiDeleteSession,
} from '@/lib/api';
import { SessionSummary, SessionType } from '@/lib/types';

export function useSessions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await listSessions();
      // Sort by updated_at descending
      const sorted = [...data].sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
      setSessions(sorted);
    } catch (err: any) {
      setError(err?.message || 'Failed to load sessions');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const create = async (type: SessionType): Promise<SessionSummary> => {
    const created = await apiCreateSession(type);
    setSessions((prev) => [created, ...prev]);
    return created;
  };

  const rename = async (id: string, title: string): Promise<SessionSummary> => {
    const updated = await apiRenameSession(id, title);
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, title: updated.title, updated_at: updated.updated_at } : s))
    );
    return updated;
  };

  const remove = async (id: string): Promise<void> => {
    await apiDeleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const updateSessionDocument = (id: string, doc: SessionSummary['document']) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, document: doc } : s))
    );
  };

  return {
    sessions,
    isLoading,
    error,
    refresh,
    create,
    rename,
    remove,
    updateSessionDocument,
  };
}
