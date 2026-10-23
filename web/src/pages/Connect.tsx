import { CheckCircle2, KeyRound, Landmark, Loader2, Unplug, Zap } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { usePlaidLink } from "react-plaid-link";
import { Button, ErrorNote, Panel, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { useRefresh, useSession } from "../lib/context";
import { accountType, money } from "../lib/format";
import { useLoad } from "../lib/hooks";

/** Opens Plaid Link once a link token exists. Mounted only then, so the Plaid script loads on demand. */
function PlaidLinkButton({
  token,
  onSuccess,
  onExit,
  onFail,
}: {
  token: string;
  onSuccess: (publicToken: string) => void;
  onExit: () => void;
  onFail: (message: string) => void;
}) {
  const { open, ready, error } = usePlaidLink({ token, onSuccess: (publicToken) => publicToken && onSuccess(publicToken), onExit });
  useEffect(() => {
    if (ready) open();
  }, [ready, open]);
  // If Plaid's script is blocked (ad blocker, school Wi-Fi), don't spin forever.
  useEffect(() => {
    if (error) return onFail("Plaid Link couldn't load. Check the connection or ad blocker, or use Quick connect.");
    const timer = setTimeout(() => !ready && onFail("Plaid Link is taking too long to load. Try again, or use Quick connect."), 15000);
    return () => clearTimeout(timer);
  }, [error, ready, onFail]);
  return (
    <Button variant="primary" disabled>
      <Loader2 size={16} className="animate-spin" /> Opening Plaid
    </Button>
  );
}

/** Plaid errors arrive as a bare code like INVALID_API_KEYS; say what to do about it. */
function explain(message: string) {
  return /^[A-Z_]+$/.test(message)
    ? `Plaid said ${message}. Run "python -m api.check_plaid" in the project folder to check your keys.`
    : message;
}

export function Connect() {
  const { session } = useSession();
  const { version, bump } = useRefresh();
  const { data, error, reload } = useLoad(() => api.dashboard(), [version]);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [busy, setBusy] = useState<"link" | "quick" | "disconnect" | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  const connected = data?.source === "Plaid Sandbox";
  const failed = data?.source.startsWith("Fake bank (Plaid failed");

  const run = useCallback(
    async (kind: "link" | "quick" | "disconnect", action: () => Promise<unknown>) => {
      setProblem(null);
      setBusy(kind);
      try {
        await action();
        bump();
      } catch (e) {
        setProblem(explain((e as Error).message));
      } finally {
        setBusy(null);
      }
    },
    [bump],
  );

  async function startLink() {
    setProblem(null);
    setBusy("link");
    try {
      const { link_token } = await api.linkToken();
      setLinkToken(link_token);
    } catch (e) {
      setProblem(explain((e as Error).message));
      setBusy(null);
    }
  }

  const finishLink = useCallback(
    (publicToken: string) => {
      setLinkToken(null);
      run("link", () => api.exchange(publicToken));
    },
    [run],
  );
  const exitLink = useCallback(() => {
    setLinkToken(null);
    setBusy(null);
  }, []);
  const failLink = useCallback((message: string) => {
    setLinkToken(null);
    setBusy(null);
    setProblem(message);
  }, []);

  const plaidReady = session?.plaid_available;
  const ownerOnly = session?.password_required && session.mode !== "owner";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="display text-3xl font-semibold">Accounts</h1>
        <p className="mt-1 max-w-2xl text-muted">
          Sensible starts on a fake bank. Connect Plaid's Sandbox to pull test accounts the way a real bank link works. No real bank logins, ever.
        </p>
      </header>

      {error && <ErrorNote message={error} onRetry={reload} />}

      <div className="grid gap-6 lg:grid-cols-12">
        <Panel className="lg:col-span-7" title="Data source">
          {!data ? (
            <Skeleton className="h-24" />
          ) : (
            <div className="space-y-5">
              <div className="flex items-center gap-4 rounded-xl bg-sunken p-4">
                <span className={`grid h-11 w-11 place-items-center rounded-xl ${connected ? "bg-series-last text-white" : "bg-mint text-mint-ink"}`}>
                  {connected ? <Landmark size={20} /> : <CheckCircle2 size={20} />}
                </span>
                <div>
                  <p className="font-semibold">{connected ? "Plaid Sandbox connected" : "Using the fake bank"}</p>
                  <p className="text-sm text-muted">
                    {connected ? "Live test data from Plaid. Refreshes every few minutes." : "Five made-up accounts and 90 days of planted transactions."}
                  </p>
                </div>
              </div>

              {failed && <ErrorNote message={`Plaid didn't answer (${data.source.match(/failed: (.*)\)$/)?.[1] ?? "error"}), so you're seeing the fake bank.`} />}
              {problem && <ErrorNote message={problem} />}

              {!plaidReady ? (
                <div className="flex gap-3 rounded-xl border border-dashed border-line p-4 text-sm">
                  <KeyRound size={18} className="mt-0.5 shrink-0 text-muted" />
                  <div>
                    <p className="font-medium">Plaid keys aren't set on this server</p>
                    <p className="mt-1 text-muted">
                      Get free Sandbox keys at dashboard.plaid.com, then add <code className="rounded bg-sunken px-1">PLAID_CLIENT_ID</code> and{" "}
                      <code className="rounded bg-sunken px-1">PLAID_SECRET</code> to <code className="rounded bg-sunken px-1">.env</code> and restart. Keys never go in the code.
                    </p>
                  </div>
                </div>
              ) : ownerOnly ? (
                <div className="flex gap-3 rounded-xl border border-dashed border-line p-4 text-sm">
                  <KeyRound size={18} className="mt-0.5 shrink-0 text-muted" />
                  <p className="text-muted">Only the owner can connect a bank here. Sign out and sign in with the owner password.</p>
                </div>
              ) : connected || failed ? (
                <Button variant="danger" disabled={busy !== null} onClick={() => run("disconnect", api.disconnect)}>
                  {busy === "disconnect" ? <Loader2 size={16} className="animate-spin" /> : <Unplug size={16} />} {connected ? "Disconnect, back to fake bank" : "Clear the failed connection"}
                </Button>
              ) : (
                <div className="flex flex-wrap gap-3">
                  {linkToken ? (
                    <PlaidLinkButton token={linkToken} onSuccess={finishLink} onExit={exitLink} onFail={failLink} />
                  ) : (
                    <Button variant="primary" disabled={busy !== null} onClick={startLink}>
                      {busy === "link" ? <Loader2 size={16} className="animate-spin" /> : <Landmark size={16} />} Connect with Plaid Link
                    </Button>
                  )}
                  <Button disabled={busy !== null} onClick={() => run("quick", api.sandboxConnect)}>
                    {busy === "quick" ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />} Quick connect test bank
                  </Button>
                </div>
              )}
              {plaidReady && !connected && !failed && !ownerOnly && (
                <p className="text-xs text-muted">
                  In Plaid Link, pick any bank and sign in with <code className="rounded bg-sunken px-1">user_good</code> /{" "}
                  <code className="rounded bg-sunken px-1">pass_good</code>. Those are Plaid's public test logins.
                </p>
              )}
            </div>
          )}
        </Panel>

        <Panel className="lg:col-span-5" title="How the link stays safe">
          <ol className="space-y-3 text-sm">
            {[
              ["Your browser gets a one-time link token", "It can open Plaid, nothing else."],
              ["Plaid hands back a public token", "Short-lived. Useless on its own."],
              ["Our server swaps it for an access token", "That token stays on the server, in memory. The browser never sees it."],
              ["Sign out and it's gone", "Nothing is written to disk or a database."],
            ].map(([title, body], i) => (
              <li key={title} className="flex gap-3">
                <span className="num grid h-6 w-6 shrink-0 place-items-center rounded-full bg-sunken text-xs font-semibold">{i + 1}</span>
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="text-muted">{body}</p>
                </div>
              </li>
            ))}
          </ol>
        </Panel>
      </div>

      {data && (
        <Panel title="Accounts in view" aside={<span className="num">{money(data.net_worth)} net worth</span>}>
          <ul className="divide-y divide-line">
            {data.accounts.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-medium">{a.name}</p>
                  <p className="text-xs text-muted">
                    {accountType[a.type] ?? a.type}, {a.institution}
                  </p>
                </div>
                <p className={`num font-semibold ${a.balance < 0 ? "text-coral-text" : ""}`}>
                  {money(a.balance)}
                  {a.type === "credit" && <span className="ml-1 text-xs font-normal text-muted">owed</span>}
                </p>
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
