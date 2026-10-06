'use client';

import { useState, useEffect } from 'react';
import { fetchPdf } from '@/lib/api';

export function usePdfBlob(sessionId: string | null, enabled: boolean) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId || !enabled) {
      setBlobUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setIsLoading(false);
      setError(null);
      return;
    }

    let isMounted = true;
    let createdUrl: string | null = null;

    async function loadBlob() {
      setIsLoading(true);
      setError(null);
      try {
        const blob = await fetchPdf(sessionId!);
        if (!isMounted) return;
        createdUrl = URL.createObjectURL(blob);
        setBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return createdUrl;
        });
      } catch (err: any) {
        if (!isMounted) return;
        console.error('Failed to fetch PDF blob:', err);
        setError(err?.message || 'Failed to load PDF preview');
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadBlob();

    return () => {
      isMounted = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [sessionId, enabled]);

  return { blobUrl, isLoading, error };
}
