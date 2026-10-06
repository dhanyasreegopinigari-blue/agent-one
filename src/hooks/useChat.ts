'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { listMessages, streamChat } from '@/lib/api';
import { ChatMessage, Source } from '@/lib/types';

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const loadMessages = useCallback(async (sid: string) => {
    try {
      setIsLoading(true);
      const data = await listMessages(sid);
      setMessages(data);
    } catch (err) {
      console.error('Failed to load messages for session:', sid, err);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      loadMessages(sessionId);
    } else {
      setMessages([]);
    }
    setCurrentStage(null);
    setIsStreaming(false);

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, [sessionId, loadMessages]);

  const send = async (text: string) => {
    if (!sessionId || !text.trim() || isStreaming) return;

    const trimmed = text.trim();
    const tempUserMsgId = `user_${Date.now()}`;
    const tempAssistantMsgId = `asst_${Date.now()}`;

    const userMessage: ChatMessage = {
      id: tempUserMsgId,
      role: 'user',
      content: trimmed,
      sources: [],
      model_used: null,
      fallback: false,
      grounded: null,
      created_at: new Date().toISOString(),
    };

    const assistantPlaceholder: ChatMessage = {
      id: tempAssistantMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      model_used: null,
      fallback: false,
      grounded: null,
      created_at: new Date().toISOString(),
      pending: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setIsStreaming(true);
    setCurrentStage('starting');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamChat(
        sessionId,
        trimmed,
        {
          status: (data) => {
            setCurrentStage(data.stage);
          },
          sources: (data) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempAssistantMsgId
                  ? { ...m, sources: (data.sources || []) as Source[] }
                  : m
              )
            );
          },
          token: (data) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempAssistantMsgId
                  ? { ...m, content: m.content + (data.text || '') }
                  : m
              )
            );
          },
          reset: () => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempAssistantMsgId ? { ...m, content: '' } : m
              )
            );
          },
          done: (data) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempAssistantMsgId
                  ? {
                      ...m,
                      id: data.message_id || m.id,
                      model_used: data.model_used,
                      fallback: Boolean(data.fallback),
                      grounded: data.grounded,
                      pending: false,
                    }
                  : m
              )
            );
          },
          error: (data) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === tempAssistantMsgId
                  ? {
                      ...m,
                      pending: false,
                      error: data.message || data.code || 'An error occurred',
                    }
                  : m
              )
            );
          },
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // Aborted by user
        setMessages((prev) => prev.filter((m) => m.id !== tempAssistantMsgId));
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempAssistantMsgId
              ? {
                  ...m,
                  pending: false,
                  error: err?.message || 'Chat stream failed',
                }
              : m
          )
        );
      }
    } finally {
      setIsStreaming(false);
      setCurrentStage(null);
      abortControllerRef.current = null;
    }
  };

  const stop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const retryLast = () => {
    // Find last user message
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      send(lastUserMsg.content);
    }
  };

  return {
    messages,
    isLoading,
    isStreaming,
    currentStage,
    send,
    stop,
    retryLast,
    reloadMessages: () => sessionId && loadMessages(sessionId),
  };
}
