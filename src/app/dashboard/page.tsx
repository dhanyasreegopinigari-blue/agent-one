'use client';

import React, { useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import AppShell from '@/components/app/AppShell';
import { Loader2 } from 'lucide-react';

function DashboardContent() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[var(--bg-canvas)] text-slate-400 font-mono text-xs gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
        <span>Authenticating session...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <AppShell />;
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="h-screen w-screen flex flex-col items-center justify-center bg-[var(--bg-canvas)] text-slate-400 font-mono text-xs gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
          <span>Loading workspace...</span>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
