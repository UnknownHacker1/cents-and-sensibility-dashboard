import { AlertTriangle, CalendarClock, Pencil, Target } from "lucide-react";
import { useState } from "react";
import type { Account, Alert, Subscription } from "../lib/api";
import { accountType, money, moneyWhole, shortDate } from "../lib/format";
import { useStored } from "../lib/hooks";
import { Panel } from "./ui";

/** Every account in one strip, with the net-worth total leading. */
export function AccountsStrip({ accounts, netWorth }: { accounts: Account[]; netWorth: number }) {
  return (
    <section aria-label="Accounts" className="flex flex-col overflow-hidden rounded-2xl border border-line bg-raised shadow-panel lg:flex-row">
      <div className="shrink-0 border-b border-line bg-ink p-5 text-bg lg:w-60 lg:border-b-0">
        <p className="text-sm opacity-75">Net worth</p>
        <p className="display num mt-1 text-3xl font-semibold">{money(netWorth)}</p>
        <p className="mt-1 text-xs opacity-75">Across {accounts.length} accounts</p>
      </div>
      <ul className="grid flex-1 grid-cols-1 sm:grid-cols-2 xl:grid-cols-[repeat(auto-fit,minmax(150px,1fr))]">
        {accounts.map((a) => (
          <li key={a.id} className="flex items-center justify-between gap-3 border-b border-line px-5 py-3 sm:block sm:border-r sm:py-4">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{a.name}</p>
              <p className="truncate text-xs text-muted">
                {accountType[a.type] ?? a.type}, {a.institution}
              </p>
            </div>
            <p className={`num text-lg font-semibold sm:mt-1.5 ${a.balance < 0 ? "text-coral-text" : ""}`}>
              {money(a.balance)}
              {a.type === "credit" && <span className="ml-1 text-xs font-normal text-muted">owed</span>}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Charges that broke the pattern. Each one can be sent straight to Money Brain. */
export function AlertsList({ alerts, onAsk }: { alerts: Alert[]; onAsk: (question: string) => void }) {
  return (
    <Panel id="alerts" title="Looks off" aside={alerts.length ? `${alerts.length} in the last 2 weeks` : undefined}>
      {alerts.length === 0 ? (
        <p className="text-sm text-muted">Nothing unusual in the last two weeks.</p>
      ) : (
        <ul className="space-y-3">
          {alerts.map((a) => (
            <li key={`${a.date}-${a.merchant}`} className="rounded-xl border-l-[3px] border-coral bg-coral-soft/60 py-3 pl-4 pr-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex gap-2.5">
                  <AlertTriangle size={16} className="mt-0.5 shrink-0 text-coral-text" aria-hidden="true" />
                  <div>
                    <p className="font-medium">{a.merchant}</p>
                    <p className="text-xs text-muted">
                      {shortDate(a.date)}, {a.category}
                    </p>
                  </div>
                </div>
                <p className="num font-semibold">{money(a.amount)}</p>
              </div>
              <p className="mt-2 pl-[26px] text-sm text-muted">{a.reason[0].toUpperCase() + a.reason.slice(1)}.</p>
              <button
                onClick={() => onAsk(`Tell me about the ${money(a.amount)} charge at ${a.merchant}. Is it normal for me?`)}
                className="mt-2 ml-[26px] text-sm font-medium text-ink underline decoration-coral decoration-2 underline-offset-4 hover:text-coral-text"
              >
                Ask about this
              </button>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function Subscriptions({ items }: { items: Subscription[] }) {
  const monthly = items.reduce((sum, s) => sum + s.amount, 0);
  return (
    <Panel title="Subscriptions" aside={items.length ? <span className="num">{money(monthly)}/mo</span> : undefined}>
      {items.length === 0 ? (
        <p className="text-sm text-muted">No repeating charges found yet.</p>
      ) : (
        <>
          <ul className="divide-y divide-line">
            {items.map((s) => (
              <li key={s.merchant} className="flex items-center justify-between gap-3 py-2.5">
                <div>
                  <p className="text-sm font-medium">{s.merchant}</p>
                  <p className="flex items-center gap-1 text-xs text-muted">
                    <CalendarClock size={12} aria-hidden="true" /> Next around {shortDate(s.next_expected)}
                  </p>
                </div>
                <p className="num text-sm font-medium">{money(s.amount)}</p>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">
            That's <span className="num font-medium text-ink">{moneyWhole(monthly * 12)}</span> a year.
          </p>
        </>
      )}
    </Panel>
  );
}

const MONTHLY_DEPOSIT = 150;

/** Savings goal. The target lives in this browser only. */
export function Goal({ saved }: { saved: number }) {
  const [target, setTarget] = useStored("sensible.goal", 5000);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(target));
  const progress = target > 0 ? Math.min(Math.max(saved / target, 0), 1) : 0;
  const left = Math.max(target - saved, 0);
  const months = Math.ceil(left / MONTHLY_DEPOSIT);

  function save() {
    const n = Number(draft.replace(/[^0-9.]/g, ""));
    if (n > 0 && n < 10_000_000) setTarget(Math.round(n));
    setEditing(false);
  }

  return (
    <Panel
      title="Emergency fund"
      aside={
        !editing && (
          <button onClick={() => (setDraft(String(target)), setEditing(true))} className="flex items-center gap-1 hover:text-ink" aria-label="Change goal">
            <Pencil size={13} /> Edit
          </button>
        )
      }
    >
      <div className="flex items-baseline justify-between">
        <p className="display num text-2xl font-semibold">{money(saved)}</p>
        {editing ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save();
            }}
            className="flex items-center gap-1 text-sm"
          >
            <span className="text-muted">of $</span>
            <input
              autoFocus
              inputMode="decimal"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={save}
              className="num w-20 rounded-md border border-line bg-bg px-2 py-0.5 outline-none focus:border-mint"
              aria-label="Goal amount"
            />
          </form>
        ) : (
          <p className="num text-sm text-muted">of {moneyWhole(target)}</p>
        )}
      </div>
      <div className="mt-3 h-3 rounded-full bg-sunken" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress * 100)} aria-label="Progress to goal">
        <div className="h-full rounded-full bg-mint transition-[width] duration-700" style={{ width: `${Math.max(progress * 100, 2)}%` }} />
      </div>
      <p className="mt-3 flex items-start gap-2 text-sm text-muted">
        <Target size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
        {left === 0 ? (
          <span>You hit it. Time to pick the next goal.</span>
        ) : (
          <span>
            <span className="num font-medium text-ink">{Math.round(progress * 100)}%</span> there. At {moneyWhole(MONTHLY_DEPOSIT)} a month you finish in{" "}
            <span className="num font-medium text-ink">{months}</span> {months === 1 ? "month" : "months"}.
          </span>
        )}
      </p>
    </Panel>
  );
}
