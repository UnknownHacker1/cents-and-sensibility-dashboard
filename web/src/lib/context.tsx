import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { api, type Session } from "./api";

type SessionState = { session: Session | null; refresh: () => Promise<Session> };
const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const refresh = useCallback(async () => {
    const s = await api.session();
    setSession(s);
    return s;
  }, []);
  useEffect(() => {
    refresh().catch(() =>
      setSession({ authenticated: false, mode: null, password_required: false, plaid_available: false, ai_engine: "rules" }),
    );
  }, [refresh]);
  return <SessionContext.Provider value={{ session, refresh }}>{children}</SessionContext.Provider>;
}

export const useSession = () => useContext(SessionContext)!;

type AskState = { open: boolean; prefill: string | null; openAsk: (prefill?: string) => void; closeAsk: () => void };
const AskContext = createContext<AskState | null>(null);

export function AskProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [prefill, setPrefill] = useState<string | null>(null);
  const openAsk = useCallback((text?: string) => {
    setPrefill(text ?? null);
    setOpen(true);
  }, []);
  const closeAsk = useCallback(() => {
    setOpen(false);
    setPrefill(null);
  }, []);
  const inApp = useLocation().pathname.startsWith("/app");
  useEffect(() => {
    if (!inApp) return; // the panel only lives inside the app
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [inApp]);
  return <AskContext.Provider value={{ open, prefill, openAsk, closeAsk }}>{children}</AskContext.Provider>;
}

export const useAsk = () => useContext(AskContext)!;

/** Pages bump this after switching data source so every view refetches. */
const RefreshContext = createContext<{ version: number; bump: () => void }>({ version: 0, bump: () => {} });

export function RefreshProvider({ children }: { children: ReactNode }) {
  const [version, setVersion] = useState(0);
  return <RefreshContext.Provider value={{ version, bump: () => setVersion((v) => v + 1) }}>{children}</RefreshContext.Provider>;
}

export const useRefresh = () => useContext(RefreshContext);
