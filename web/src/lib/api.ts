// Talks to the FastAPI backend. Same origin in production; Vite proxies /api in dev.

export type StoryToken = { text: string } | { value: string; kind: "spent" | "change_up" | "change_down" | "category" | "alert" };

export type Account = { id: string; name: string; type: "checking" | "savings" | "credit" | "investment"; institution: string; balance: number };
export type PacePoint = { day: number; this_month: number | null; last_month: number | null };
export type Alert = { date: string; merchant: string; category: string; amount: number; reason: string };
export type Subscription = { merchant: string; amount: number; months_seen: number; last_charged: string; next_expected: string };
export type Transaction = { date: string; merchant: string; category: string; account: string; account_id: string; amount: number };

export type Dashboard = {
  source: string;
  month: string;
  months: { value: string; label: string }[];
  story: StoryToken[];
  net_worth: number;
  accounts: Account[];
  summary: { spent: number; income: number; net: number; top_category: string | null; change_pct: number | null };
  by_category: { category: string; amount: number }[];
  pace: PacePoint[];
  subscriptions: Subscription[];
  alerts: Alert[];
  goal: { saved: number };
};

export type Preview = {
  story: StoryToken[];
  pace: PacePoint[];
  alerts: Alert[];
  examples: { question: string; answer: string }[];
};

export type Session = {
  authenticated: boolean;
  mode: "owner" | "demo" | null;
  password_required: boolean;
  plaid_available: boolean;
  ai_engine: "claude" | "rules";
};

export type SecurityCheck = {
  id: string;
  title: string;
  status: "pass" | "warn" | "fail";
  detail: string;
  attacks?: { prompt: string; blocked: boolean; reply: string }[];
};

export type AskEvent =
  | { type: "meta"; engine: "claude" | "rules"; refused: boolean }
  | { type: "delta"; text: string }
  | { type: "done" };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Something went wrong. Try again.";
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  session: () => request<Session>("/api/session"),
  login: (body: { password?: string; demo?: boolean }) => post<{ mode: string }>("/api/login", body),
  logout: () => post("/api/logout"),
  preview: () => request<Preview>("/api/preview"),
  dashboard: (month?: string) => request<Dashboard>(`/api/dashboard${month ? `?month=${month}` : ""}`),
  transactions: (params: { q?: string; category?: string; account?: string }) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]);
    return request<Transaction[]>(`/api/transactions?${query}`);
  },
  security: () => request<SecurityCheck[]>("/api/security"),
  linkToken: () => post<{ link_token: string }>("/api/plaid/link-token"),
  exchange: (public_token: string) => post<{ source: string }>("/api/plaid/exchange", { public_token }),
  sandboxConnect: () => post<{ source: string }>("/api/plaid/sandbox-connect"),
  disconnect: () => post<{ source: string }>("/api/plaid/disconnect"),
};

/** Streams Money Brain's answer. Calls onEvent for each Server-Sent Event. */
export async function ask(
  question: string,
  history: { role: "user" | "assistant"; content: string }[],
  onEvent: (event: AskEvent) => void,
): Promise<void> {
  const response = await fetch("/api/ask", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history: history.slice(-8) }),
  });
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, typeof body.detail === "string" ? body.detail : "Money Brain is unavailable.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      if (chunk.startsWith("data: ")) onEvent(JSON.parse(chunk.slice(6)) as AskEvent);
    }
  }
}
