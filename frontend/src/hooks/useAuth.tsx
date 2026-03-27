import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import { api } from "../api/client";
import { clearStoredSession, getStoredSession, setStoredSession } from "../lib/storage";
import type { AuthSession, User } from "../types/api";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signInWithGoogle: () => Promise<void>;
  completeGoogleCallback: (code: string, state: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<AuthSession | null>(() => getStoredSession());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      const stored = getStoredSession();
      if (!stored) {
        if (active) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const user = await api.getMe();
        if (!active) {
          return;
        }
        const nextSession = { ...stored, user };
        setStoredSession(nextSession);
        setSession(nextSession);
      } catch {
        clearStoredSession();
        if (active) {
          setSession(null);
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void bootstrap();

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      isAuthenticated: Boolean(session),
      isLoading,
      async signInWithGoogle() {
        const redirectHint = `${window.location.origin}/auth/callback`;
        const response = await api.getGoogleLogin(redirectHint);
        window.location.href = response.authorization_url;
      },
      async completeGoogleCallback(code: string, state: string) {
        const nextSession = await api.completeGoogleCallback({ code, state });
        setStoredSession(nextSession);
        setSession(nextSession);
      },
      logout() {
        clearStoredSession();
        setSession(null);
      },
      async refreshUser() {
        if (!session) {
          return;
        }
        const user = await api.getMe();
        const nextSession = { ...session, user };
        setStoredSession(nextSession);
        setSession(nextSession);
      },
    }),
    [isLoading, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
