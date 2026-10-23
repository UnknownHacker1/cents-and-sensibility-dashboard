import { Brain } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { CategoryBars, PaceChart } from "../components/charts";
import { Story } from "../components/Story";
import { Panel, Skeleton, ErrorNote } from "../components/ui";
import { AccountsStrip, AlertsList, Goal, Subscriptions } from "../components/widgets";
import { api } from "../lib/api";
import { useAsk, useRefresh } from "../lib/context";
import { money, monthName } from "../lib/format";
import { useLoad } from "../lib/hooks";

function OverviewSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true">
      <Skeleton className="h-6 w-40" />
      <Skeleton className="h-28 w-full max-w-3xl" />
      <Skeleton className="h-28 w-full" />
      <div className="grid gap-6 lg:grid-cols-12">
        <Skeleton className="h-80 lg:col-span-8" />
        <Skeleton className="h-80 lg:col-span-4" />
      </div>
    </div>
  );
}

export function Overview() {
  const [month, setMonth] = useState<string | undefined>(undefined);
  const { version } = useRefresh();
  const { openAsk } = useAsk();
  const { data, error, reload } = useLoad(() => api.dashboard(month), [month, version]);

  if (error) return <ErrorNote message={error} onRetry={reload} />;
  if (!data) return <OverviewSkeleton />;

  const thisLabel = monthName(data.month);
  const lastLabel = monthName(data.month, -1);
  const isLatest = data.month === data.months[0]?.value; // newest first
  const { summary } = data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-sm text-muted">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-raised px-2.5 py-1">
            <span className={`h-1.5 w-1.5 rounded-full ${data.source === "Plaid Sandbox" ? "bg-series-last" : "bg-mint"}`} aria-hidden="true" />
            {data.source}
          </span>
          {data.source !== "Plaid Sandbox" && (
            <Link to="/app/connect" className="hover:text-ink hover:underline">
              Connect a sandbox bank
            </Link>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted">Month</span>
          <select
            value={data.month}
            onChange={(e) => setMonth(e.target.value)}
            className="rounded-[10px] border border-line bg-raised px-3 py-1.5 font-medium outline-none focus:border-mint"
          >
            {data.months.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <section aria-label="Your month" className="pb-2 pt-2 lg:pt-4">
        <Story key={data.month + data.source} tokens={data.story} onAlertClick={() => document.getElementById("alerts")?.scrollIntoView({ behavior: "smooth" })} />
        <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted">
          <span>
            Income <strong className="num font-semibold text-good">{money(summary.income)}</strong>
          </span>
          <span>
            Left over <strong className={`num font-semibold ${summary.net < 0 ? "text-coral-text" : "text-ink"}`}>{money(summary.net)}</strong>
          </span>
          <button onClick={() => openAsk(`Why did I spend ${money(summary.spent)} in ${thisLabel}?`)} className="inline-flex items-center gap-1.5 font-medium text-ink hover:underline">
            <Brain size={15} /> Ask why
          </button>
        </div>
      </section>

      <AccountsStrip accounts={data.accounts} netWorth={data.net_worth} />

      <div className="grid gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-8">
          <Panel title={isLatest ? "Spending pace" : `Spending through ${thisLabel}`} aside={isLatest ? `${thisLabel} so far vs ${lastLabel}` : undefined}>
            <PaceChart data={data.pace} thisLabel={thisLabel} lastLabel={lastLabel} />
          </Panel>
          <Panel title="Where it went" aside={<span className="num">{money(summary.spent)} total</span>}>
            <CategoryBars rows={data.by_category} />
          </Panel>
        </div>
        <div className="space-y-6 lg:col-span-4">
          <AlertsList alerts={data.alerts} onAsk={openAsk} />
          <Subscriptions items={data.subscriptions} />
          <Goal saved={data.goal.saved} />
        </div>
      </div>
    </div>
  );
}
