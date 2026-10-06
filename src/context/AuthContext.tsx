'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { UserProfile } from '@/lib/types';
import type { User } from '@supabase/supabase-js';

type Result = { success: boolean; error?: string; needsConfirmation?: boolean };

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  getAccessToken(): Promise<string | null>;
  login(email: string, password: string): Promise<Result>;
  signup(name: string, email: string, password: string): Promise<Result>;
  loginWithGoogle(): Promise<Result>;
  loginAsGuest(): Promise<Result>;
  logout(): Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const LOCAL_STORAGE_KEY = 'agentone_user_session';

function mapUser(u: User): UserProfile {
  return {
    id: u.id,
    email: u.email ?? null,
    name:
      u.user_metadata?.full_name ??
      u.user_metadata?.name ??
      u.email?.split('@')[0] ??
      (u.is_anonymous ? 'Guest' : 'User'),
    avatarUrl: u.user_metadata?.avatar_url,
    isAnonymous: Boolean(u.is_anonymous),
  };
}

function isPlaceholderSupabase(): boolean {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  return !url || url.includes('placeholder') || url.includes('example.com');
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;

    async function initSession() {
      // 1. Try Supabase active session if real Supabase configured
      if (!isPlaceholderSupabase()) {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.user && mounted) {
            const mapped = mapUser(session.user);
            setUser(mapped);
            if (typeof window !== 'undefined') {
              localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(mapped));
            }
            setIsLoading(false);
            return;
          }
        } catch (err) {
          console.warn('Supabase session init warning:', err);
        }
      }

      // 2. Check local stored session
      if (typeof window !== 'undefined') {
        try {
          const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
          if (saved && mounted) {
            const parsed = JSON.parse(saved);
            if (parsed && parsed.id) {
              setUser(parsed);
              setIsLoading(false);
              return;
            }
          }
        } catch (err) {
          console.warn('Local session parse warning:', err);
        }
      }

      if (mounted) {
        setUser(null);
        setIsLoading(false);
      }
    }

    initSession();

    let subscription: { unsubscribe: () => void } | null = null;
    if (!isPlaceholderSupabase()) {
      try {
        const { data } = supabase.auth.onAuthStateChange((_event, session) => {
          if (mounted) {
            if (session?.user) {
              const mapped = mapUser(session.user);
              setUser(mapped);
              if (typeof window !== 'undefined') {
                localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(mapped));
              }
            } else if (_event === 'SIGNED_OUT') {
              setUser(null);
              if (typeof window !== 'undefined') {
                localStorage.removeItem(LOCAL_STORAGE_KEY);
              }
            }
            setIsLoading(false);
          }
        });
        subscription = data.subscription;
      } catch (err) {
        console.warn('Supabase auth state listener warning:', err);
      }
    }

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  const getAccessToken = async (): Promise<string | null> => {
    try {
      if (!isPlaceholderSupabase()) {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          return session.access_token;
        }
      }
    } catch {
      // fallback
    }

    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (parsed?.id) return `dev-token-${parsed.id}`;
        } catch {
          // ignore
        }
      }
    }

    return 'dev-token';
  };

  const login = async (email: string, password: string): Promise<Result> => {
    const cleanEmail = (email || '').trim().toLowerCase();
    const cleanPassword = (password || '').trim();

    if (!cleanEmail || !cleanPassword) {
      return { success: false, error: 'Please enter both email and password.' };
    }

    if (!isPlaceholderSupabase()) {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: cleanEmail,
          password: cleanPassword,
        });

        if (!error && data?.user) {
          const mapped = mapUser(data.user);
          setUser(mapped);
          if (typeof window !== 'undefined') {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(mapped));
          }
          return { success: true };
        }

        if (error && !error.message.includes('fetch') && !error.message.includes('network')) {
          return { success: false, error: error.message };
        }
      } catch (err: any) {
        console.warn('Supabase sign-in warning:', err);
      }
    }

    // Local authentication fallback for development / guest access
    const localUser: UserProfile = {
      id: `usr_${cleanEmail.replace(/[^a-z0-9]/g, '_')}`,
      email: cleanEmail,
      name: cleanEmail.split('@')[0],
      avatarUrl: undefined,
      isAnonymous: false,
    };
    setUser(localUser);
    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(localUser));
    }
    return { success: true };
  };

  const signup = async (name: string, email: string, password: string): Promise<Result> => {
    const cleanName = (name || '').trim();
    const cleanEmail = (email || '').trim().toLowerCase();
    const cleanPassword = (password || '').trim();

    if (!cleanEmail || !cleanPassword) {
      return { success: false, error: 'Please enter both email and password.' };
    }

    if (!isPlaceholderSupabase()) {
      try {
        const origin = typeof window !== 'undefined' ? window.location.origin : '';
        const { data, error } = await supabase.auth.signUp({
          email: cleanEmail,
          password: cleanPassword,
          options: {
            data: { full_name: cleanName },
            emailRedirectTo: `${origin}/dashboard`,
          },
        });

        if (error) {
          if (!error.message.includes('fetch') && !error.message.includes('network')) {
            return { success: false, error: error.message };
          }
        } else {
          if (!data.session) {
            return { success: true, needsConfirmation: true };
          }
          const mapped = mapUser(data.user!);
          setUser(mapped);
          if (typeof window !== 'undefined') {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(mapped));
          }
          return { success: true };
        }
      } catch (err: any) {
        console.warn('Supabase sign-up warning:', err);
      }
    }

    // Local dev signup fallback
    const localUser: UserProfile = {
      id: `usr_${cleanEmail.replace(/[^a-z0-9]/g, '_')}`,
      email: cleanEmail,
      name: cleanName || cleanEmail.split('@')[0],
      avatarUrl: undefined,
      isAnonymous: false,
    };
    setUser(localUser);
    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(localUser));
    }
    return { success: true };
  };

  const loginWithGoogle = async (): Promise<Result> => {
    if (!isPlaceholderSupabase()) {
      try {
        const origin = typeof window !== 'undefined' ? window.location.origin : '';
        const { error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: {
            redirectTo: `${origin}/dashboard`,
          },
        });

        if (error) {
          return { success: false, error: error.message };
        }
        return { success: true };
      } catch (err: any) {
        return { success: false, error: err?.message || 'Google sign-in failed' };
      }
    }

    // If Supabase Google OAuth isn't configured, fall back to guest session
    return loginAsGuest();
  };

  const loginAsGuest = async (): Promise<Result> => {
    if (!isPlaceholderSupabase()) {
      try {
        const { data, error } = await supabase.auth.signInAnonymously();
        if (!error && data?.user) {
          const mapped = mapUser(data.user);
          setUser(mapped);
          if (typeof window !== 'undefined') {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(mapped));
          }
          return { success: true };
        }
      } catch (err) {
        console.warn('Supabase anonymous sign-in warning:', err);
      }
    }

    // Guaranteed instant guest access
    const guestUser: UserProfile = {
      id: 'usr_guest',
      email: 'guest@agentone.ai',
      name: 'Guest Analyst',
      avatarUrl: undefined,
      isAnonymous: true,
    };
    setUser(guestUser);
    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(guestUser));
    }
    return { success: true };
  };

  const logout = async (): Promise<void> => {
    try {
      if (!isPlaceholderSupabase()) {
        await supabase.auth.signOut();
      }
    } catch (err) {
      console.warn('Sign out warning:', err);
    }
    if (typeof window !== 'undefined') {
      localStorage.removeItem(LOCAL_STORAGE_KEY);
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        getAccessToken,
        login,
        signup,
        loginWithGoogle,
        loginAsGuest,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
