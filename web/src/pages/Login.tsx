import { Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Wordmark } from "../components/ui";
import { api } from "../lib/api";
import { useSession } from "../lib/context";

export function Login() {
  const { session, refresh } = useSession();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState<"owner" | "demo" | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  async function signIn(body: { password?: string; demo?: boolean }, kind: "owner" | "demo") {
    setProblem(null);
    setBusy(kind);
    try {
      await api.login(body);
      await refresh();
      navigate("/app");
    } catch (e) {
      setProblem((e as Error).message);
      setBusy(null);
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (password) signIn({ password }, "owner");
  };

  return (
    <div className="grid min-h-screen place-items-center px-4 py-10">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-10 block w-fit">
          <Wordmark />
        </Link>
        <h1 className="display text-3xl font-semibold">Come on in.</h1>
        <p className="mt-2 text-muted">The demo runs on a fake bank, so there's nothing real to protect yet. Look around.</p>

        <Button variant="primary" className="mt-8 w-full py-3 text-base" disabled={busy !== null} onClick={() => signIn({ demo: true }, "demo")}>
          {busy === "demo" && <Loader2 size={18} className="animate-spin" />} Explore with demo data
        </Button>

        {session?.password_required && (
          <form onSubmit={onSubmit} className="mt-8 border-t border-line pt-8">
            <label htmlFor="password" className="text-sm font-medium">
              Owner password
            </label>
            <p className="mt-0.5 text-xs text-muted">Needed to connect a Plaid Sandbox bank.</p>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-2 w-full rounded-[10px] border border-line bg-raised px-3 py-2.5 outline-none focus:border-mint"
            />
            <Button type="submit" className="mt-3 w-full" disabled={busy !== null || !password}>
              {busy === "owner" && <Loader2 size={16} className="animate-spin" />} Sign in as owner
            </Button>
          </form>
        )}

        {problem && (
          <p role="alert" className="mt-4 text-sm text-coral-text">
            {problem}
          </p>
        )}
      </div>
    </div>
  );
}
