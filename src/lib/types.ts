export type SessionType = 'pdf' | 'web';
export type IngestStatus = 'processing' | 'ready' | 'failed';

export interface DocumentInfo {
  filename: string;
  size_bytes: number;
  page_count: number | null;
  n_chunks: number | null;
  status: IngestStatus;
  stage: string;
  progress: number;
  error_code: string | null;
  error_message: string | null;
}

export interface SessionSummary {
  id: string;
  type: SessionType;
  title: string;
  created_at: string;
  updated_at: string;
  document: DocumentInfo | null;
}

export interface Region {
  page: number;
  bbox: [number, number, number, number]; // normalized 0..1
}

export interface PdfSource {
  id: string;
  chunk_id: number;
  page_start: number;
  page_end: number;
  snippet: string;
  score: number;
  regions: Region[];
}

export interface WebSource {
  id: string;
  title: string;
  url: string;
  snippet: string;
}

export type Source = PdfSource | WebSource;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[];
  model_used: string | null;
  fallback: boolean;
  grounded: boolean | null;
  created_at: string;
  pending?: boolean;
  error?: string;
}

export interface UserProfile {
  id: string;
  email: string | null;
  name: string;
  avatarUrl?: string;
  isAnonymous: boolean;
}

export interface Health {
  status: 'ok' | 'degraded';
  ollama: any;
  gemini: any;
  web_search: any;
  version: string;
}
