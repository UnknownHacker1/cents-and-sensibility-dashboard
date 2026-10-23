import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./api";
import { useSession } from "./context";

type Theme = "light" | "dark";

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

/** A value remembered in this browser only (theme, savings target). Never anything sensitive. */
export function useStored<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(() => readStored(key, fallback));
  const touched = useRef(false);
  useEffect(() => {
    // Only save what the person chose; untouched defaults stay defaults (and follow the system theme).
    if (!touched.current) {
      touched.current = true;
      return;
    }
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* private mode: keep it in memory only */
    }
  }, [key, value]);
  return [value, setValue] as const;
}

export function useTheme() {
  const system: Theme = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const [theme, setTheme] = useStored<Theme>("sensible.theme", system);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), [setTheme]);
  return { theme, toggle };
}

/** Load something async with loading and error state; `reload` refetches. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const { refresh } = useSession();
  useEffect(() => {
    let alive = true;
    setError(null);
    load()
      .then((d) => alive && setData(d))
      .catch((e: Error) => {
        if (!alive) return;
        // Session expired or the server restarted: re-check, and the router sends us to sign-in.
        if (e instanceof ApiError && e.status === 401) refresh().catch(() => {});
        setError(e.message);
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { data, error, reload: () => setTick((t) => t + 1) };
}

export function usePrefersReducedMotion() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}
