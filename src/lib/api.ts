import { supabase } from '@/lib/supabaseClient';
import {
  ChatMessage,
  DocumentInfo,
  Health,
  SessionSummary,
  SessionType,
} from '@/lib/types';

const BASE = (process.env.NEXT_PUBLIC_BACKEND_URL ?? '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function token(): Promise<string> {
  const { data } = await supabase.auth.getSession();
  if (!data.session) throw new ApiError(401, 'UNAUTHENTICATED', 'Please sign in');
  return data.session.access_token;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const t = await token();
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
    Authorization: `Bearer ${t}`,
  };

  if (init.body && !(init.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
  });

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(
      res.status,
      body?.error?.code ?? 'ERROR',
      body?.error?.message ?? res.statusText
    );
  }
  return body as T;
}

export async function listSessions(): Promise<SessionSummary[]> {
  return request<SessionSummary[]>('/sessions');
}

export async function createSession(type: SessionType): Promise<SessionSummary> {
  return request<SessionSummary[]>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ type }),
  }) as unknown as Promise<SessionSummary>;
}

export async function getSession(id: string): Promise<SessionSummary> {
  return request<SessionSummary>(`/sessions/${id}`);
}

export async function renameSession(id: string, title: string): Promise<SessionSummary> {
  return request<SessionSummary>(`/sessions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(id: string): Promise<void> {
  return request<void>(`/sessions/${id}`, {
    method: 'DELETE',
  });
}

export async function listMessages(sessionId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/sessions/${sessionId}/messages`);
}

export async function getStatus(sessionId: string): Promise<DocumentInfo> {
  return request<DocumentInfo>(`/sessions/${sessionId}/status`);
}

export async function fetchPdf(sessionId: string): Promise<Blob> {
  const t = await token();
  const res = await fetch(`${BASE}/sessions/${sessionId}/document`, {
    headers: {
      Authorization: `Bearer ${t}`,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(
      res.status,
      body?.error?.code ?? 'ERROR',
      body?.error?.message ?? res.statusText
    );
  }

  return res.blob();
}

export async function reindex(sessionId: string): Promise<void> {
  return request<void>(`/sessions/${sessionId}/reindex`, {
    method: 'POST',
  });
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) {
    throw new ApiError(res.status, 'HEALTH_CHECK_FAILED', res.statusText);
  }
  return res.json();
}

export async function uploadDocument(
  sessionId: string,
  file: File,
  onProgress?: (loaded: number, total: number) => void
): Promise<SessionSummary> {
  const t = await token();

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE}/sessions/${sessionId}/document`);
    xhr.setRequestHeader('Authorization', `Bearer ${t}`);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress(event.loaded, event.total);
        }
      };
    }

    xhr.onload = () => {
      let body: any = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // response might not be json
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as SessionSummary);
      } else {
        const code = body?.error?.code ?? 'UPLOAD_FAILED';
        const msg = body?.error?.message ?? xhr.statusText ?? 'Upload failed';
        reject(new ApiError(xhr.status, code, msg));
      }
    };

    xhr.onerror = () => {
      reject(new ApiError(0, 'NETWORK_ERROR', 'Network error during upload'));
    };

    xhr.onabort = () => {
      reject(new ApiError(0, 'ABORTED', 'Upload aborted'));
    };

    const formData = new FormData();
    formData.append('file', file);
    xhr.send(formData);
  });
}

export type SseHandlers = {
  status?: (data: { stage: string }) => void;
  sources?: (data: { sources: any[] }) => void;
  token?: (data: { text: string }) => void;
  reset?: (data: Record<string, never>) => void;
  done?: (data: {
    message_id: string;
    model_used: string | null;
    fallback: boolean;
    grounded: boolean | null;
    cited: string[];
  }) => void;
  error?: (data: { code: string; message: string }) => void;
  [event: string]: ((data: any) => void) | undefined;
};

export async function streamChat(
  sessionId: string,
  message: string,
  handlers: SseHandlers,
  signal?: AbortSignal
): Promise<void> {
  const t = await token();
  const res = await fetch(`${BASE}/sessions/${sessionId}/chat`, {
    method: 'POST',
    signal,
    headers: {
      Authorization: `Bearer ${t}`,
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const b = await res.json().catch(() => null);
    throw new ApiError(
      res.status,
      b?.error?.code ?? 'ERROR',
      b?.error?.message ?? res.statusText
    );
  }

  if (!res.body) {
    throw new ApiError(500, 'NO_RESPONSE_BODY', 'No response stream body');
  }

  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = '';

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });

      let i: number;
      while ((i = buf.indexOf('\n\n')) !== -1) {
        const frame = buf.slice(0, i);
        buf = buf.slice(i + 2);
        if (frame.startsWith(':')) continue; // heartbeat

        const ev = /^event: (.+)$/m.exec(frame)?.[1];
        const dataStr = /^data: (.+)$/m.exec(frame)?.[1];
        if (ev && dataStr) {
          try {
            const data = JSON.parse(dataStr);
            handlers[ev]?.(data);
          } catch {
            // malformed json in frame data
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
