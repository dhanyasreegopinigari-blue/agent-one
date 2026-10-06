'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { getStatus } from '@/lib/api';
import { DocumentInfo } from '@/lib/types';

export function useIngestion(
  sessionId: string | null,
  initialDoc: DocumentInfo | null = null,
  onDocChange?: (doc: DocumentInfo | null) => void
) {
  const [document, setDocumentState] = useState<DocumentInfo | null>(initialDoc);
  const onDocChangeRef = useRef(onDocChange);

  useEffect(() => {
    onDocChangeRef.current = onDocChange;
  }, [onDocChange]);

  useEffect(() => {
    setDocumentState(initialDoc);
  }, [sessionId, initialDoc]);

  const setDocument = useCallback(
    (doc: DocumentInfo | null) => {
      setDocumentState(doc);
      onDocChangeRef.current?.(doc);
    },
    []
  );

  const retry = useCallback(() => {
    setDocument(null);
  }, [setDocument]);

  useEffect(() => {
    if (!sessionId || !document || document.status !== 'processing') {
      return;
    }

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const status = await getStatus(sessionId);
        if (!isMounted) return;

        setDocumentState(status);
        onDocChangeRef.current?.(status);

        if (status.status === 'ready' || status.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.warn('Error polling ingestion status:', err);
      }
    }, 1500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sessionId, document]);

  return {
    document,
    setDocument,
    retry,
  };
}
