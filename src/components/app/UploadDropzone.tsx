'use client';

import React, { useState, useRef } from 'react';
import { uploadDocument, ApiError } from '@/lib/api';
import { SessionSummary } from '@/lib/types';
import { UploadCloud, FileText, AlertTriangle, Loader2 } from 'lucide-react';

interface UploadDropzoneProps {
  sessionId: string;
  onUploaded: (session: SessionSummary) => void;
}

const ERROR_MESSAGES: Record<string, string> = {
  NOT_A_PDF: "That file isn't a PDF.",
  FILE_TOO_LARGE: 'PDFs can be up to 50 MB.',
  PDF_ENCRYPTED: 'This PDF is password-protected.',
  PDF_NO_TEXT: 'This PDF has no selectable text (it may be a scan).',
  PDF_TOO_MANY_PAGES: 'This PDF has too many pages (max 500).',
  EMBEDDING_UNAVAILABLE: 'The AI service is unavailable. Please try again shortly.',
  BUSY: 'Please wait for the current answer to finish.',
};

export default function UploadDropzone({
  sessionId,
  onUploaded,
}: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setErrorMessage(null);

    // Client-side validations
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setErrorMessage(ERROR_MESSAGES.NOT_A_PDF);
      return;
    }

    const maxBytes = 50 * 1024 * 1024;
    if (file.size > maxBytes) {
      setErrorMessage(ERROR_MESSAGES.FILE_TOO_LARGE);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const session = await uploadDocument(sessionId, file, (loaded, total) => {
        if (total > 0) {
          setUploadProgress(Math.round((loaded / total) * 100));
        }
      });
      onUploaded(session);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(ERROR_MESSAGES[err.code] || err.message || 'Upload failed');
      } else {
        setErrorMessage(err?.message || 'Failed to upload PDF');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto p-4 sm:p-6 text-center">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-10 transition-all cursor-pointer select-none ${
          isDragging
            ? 'border-emerald-500 bg-emerald-500/10'
            : 'border-black/15 dark:border-white/15 hover:border-emerald-500/50 hover:bg-black/[0.02] dark:hover:bg-white/[0.02]'
        } ${isUploading ? 'pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          className="hidden"
        />

        {isUploading ? (
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 mx-auto flex items-center justify-center">
              <Loader2 className="w-7 h-7 animate-spin" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-[#0F172A] dark:text-white mb-1">
                Uploading PDF... {uploadProgress}%
              </h3>
              <p className="text-xs text-slate-500 font-mono">
                Transferring document to secure processing pipeline
              </p>
            </div>
            {/* Progress bar */}
            <div className="w-full h-1.5 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center">
              <UploadCloud className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-[#0F172A] dark:text-white mb-1">
                Upload a PDF document
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto leading-relaxed">
                Drag and drop your file here, or click to browse. Max size 50 MB (up to 500 pages).
              </p>
            </div>
            <div className="pt-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#0c3822] text-white border border-emerald-500/40 shadow-xs">
                <FileText className="w-3.5 h-3.5" />
                Select PDF File
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div className="mt-4 p-3 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2 text-left animate-in fade-in">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
