import { Brain, Landmark, LayoutDashboard, LogOut, Moon, ReceiptText, ShieldCheck, Sun } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAsk, useSession } from "../lib/context";
import { useTheme } from "../lib/hooks";
import { AskPanel } from "./AskPanel";
import { Wordmark } from "./ui";

const NAV = [
  { to: "/app", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/app/transactions", label: "Transactions", icon: ReceiptText },
  { to: "/app/connect", label: "Accounts", icon: Landmark },
  { to: "/app/security", label: "Security", icon: ShieldCheck },
];

export function AppShell() {
  const { theme, toggle } = useTheme();
  const { open: asking, openAsk } = useAsk();
  const { session, refresh } = useSession();
  const navigate = useNavigate();

  async function signOut() {
    await api.logout();
    await refresh();
    navigate("/");
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-[10px] px-3 py-2 text-sm font-medium transition ${
      isActive ? "bg-raised text-ink shadow-panel" : "text-muted hover:bg-raised/60 hover:text-ink"
    }`;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      {/* Side rail on desktop */}
      <aside inert={asking} className="sticky top-0 hidden h-screen flex-col gap-1 border-r border-line px-4 py-5 lg:flex">
        <NavLink to="/" className="mb-6 px-2">
          <Wordmark />
        </NavLink>
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={linkClass}>
            <Icon size={18} /> {label}
          </NavLink>
        ))}
        <button onClick={() => openAsk()} className="mt-4 flex items-center justify-between rounded-[10px] bg-ink px-3 py-2.5 text-sm font-medium text-bg hover:opacity-90">
          <span className="flex items-center gap-2.5 whitespace-nowrap">
            <Brain size={18} /> Ask Money Brain
          </span>
          <kbd className="whitespace-nowrap rounded bg-bg/15 px-1.5 text-[11px]">Ctrl K</kbd>
        </button>
        <div className="mt-auto space-y-1 border-t border-line pt-4">
          <p className="px-3 pb-2 text-xs text-muted">{session?.mode === "owner" ? "Signed in as owner" : "Exploring demo data"}</p>
          <button onClick={toggle} className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2 text-sm text-muted hover:bg-raised hover:text-ink">
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />} {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
          <button onClick={signOut} className="flex w-full items-center gap-3 rounded-[10px] px-3 py-2 text-sm text-muted hover:bg-raised hover:text-ink">
            <LogOut size={18} /> Sign out
          </button>
        </div>
      </aside>

      {/* Top bar on phones */}
      <header inert={asking} className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-bg/90 px-4 py-3 backdrop-blur lg:hidden">
        <NavLink to="/">
          <Wordmark className="text-lg" />
        </NavLink>
        <div className="flex items-center gap-1">
          <button onClick={toggle} aria-label="Toggle dark mode" className="rounded-lg p-2 text-muted hover:bg-sunken">
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button onClick={signOut} aria-label="Sign out" className="rounded-lg p-2 text-muted hover:bg-sunken">
            <LogOut size={18} />
          </button>
        </div>
      </header>

      <main inert={asking} className="mx-auto w-full max-w-[1180px] px-4 pb-28 pt-6 sm:px-6 lg:px-10 lg:pb-12 lg:pt-10">
        <Outlet />
      </main>

      {/* Bottom tabs on phones */}
      <nav inert={asking} className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-raised/95 px-1 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden">
        {NAV.slice(0, 2).map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `flex flex-col items-center gap-0.5 py-2 text-[11px] ${isActive ? "text-ink" : "text-muted"}`}>
            <Icon size={20} /> {label}
          </NavLink>
        ))}
        <button onClick={() => openAsk()} className="flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium text-ink">
          <span className="-mt-5 grid h-11 w-11 place-items-center rounded-2xl bg-ink text-bg shadow-panel">
            <Brain size={20} />
          </span>
          Ask
        </button>
        {NAV.slice(2).map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `flex flex-col items-center gap-0.5 py-2 text-[11px] ${isActive ? "text-ink" : "text-muted"}`}>
            <Icon size={20} /> {label}
          </NavLink>
        ))}
      </nav>

      <AskPanel />
    </div>
  );
}
