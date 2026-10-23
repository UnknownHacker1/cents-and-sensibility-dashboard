import { AlertTriangle, CheckCircle2, RefreshCw, ShieldCheck, XCircle } from "lucide-react";
import { Button, ErrorNote, Panel, Skeleton } from "../components/ui";
import { api, type SecurityCheck } from "../lib/api";
import { useLoad } from "../lib/hooks";

const statusIcon = {
  pass: <CheckCircle2 size={18} className="text-good" aria-label="Pass" />,
  warn: <AlertTriangle size={18} className="text-[#b7791f] dark:text-[#f6c25b]" aria-label="Warning" />,
  fail: <XCircle size={18} className="text-coral-text" aria-label="Fail" />,
};

const statusWord = { pass: "Pass", warn: "Heads up", fail: "Fail" };

function RedTeam({ attacks }: { attacks: NonNullable<SecurityCheck["attacks"]> }) {
  return (
    <div className="mt-3 overflow-x-auto rounded-xl border border-line">
      <table className="w-full text-sm">
        <thead className="bg-sunken text-left text-muted">
          <tr>
            <th className="px-3 py-2 font-medium">Attack prompt</th>
            <th className="px-3 py-2 font-medium">Result</th>
            <th className="hidden px-3 py-2 font-medium md:table-cell">What Money Brain said</th>
          </tr>
        </thead>
        <tbody>
          {attacks.map((a) => (
            <tr key={a.prompt} className="border-t border-line align-top">
              <td className="px-3 py-2 font-medium">"{a.prompt}"</td>
              <td className="whitespace-nowrap px-3 py-2">
                {a.blocked ? (
                  <span className="inline-flex items-center gap-1 text-good">
                    <ShieldCheck size={14} /> Blocked
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-coral-text">
                    <XCircle size={14} /> Got through
                  </span>
                )}
              </td>
              <td className="hidden px-3 py-2 text-muted md:table-cell">{a.reply}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Security() {
  const { data, error, reload } = useLoad(() => api.security(), []);
  const passing = data?.filter((c) => c.status === "pass").length ?? 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="display text-3xl font-semibold">Security Center</h1>
          <p className="mt-1 max-w-2xl text-muted">The app checks itself, live. Every row below is computed on the server right now, including a red-team run against Money Brain.</p>
        </div>
        <Button onClick={reload}>
          <RefreshCw size={16} /> Run again
        </Button>
      </header>

      {error && <ErrorNote message={error} onRetry={reload} />}

      {!data ? (
        <Skeleton className="h-96" />
      ) : (
        <>
          <section className="flex flex-wrap items-center gap-6 rounded-2xl border border-line bg-raised p-6 shadow-panel">
            <div className="relative h-24 w-24">
              <svg viewBox="0 0 36 36" className="h-24 w-24 -rotate-90" aria-hidden="true">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--sunken)" strokeWidth="3.5" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  stroke="var(--mint)"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeDasharray={`${(passing / data.length) * 97.4} 97.4`}
                />
              </svg>
              <span className="display num absolute inset-0 grid place-items-center text-2xl font-semibold">
                {passing}/{data.length}
              </span>
            </div>
            <div>
              <p className="display text-2xl font-semibold">
                {passing} of {data.length} checks pass
              </p>
              <p className="mt-1 text-muted">
                {passing === data.length
                  ? "Everything on the list is locked down."
                  : "The heads-up items are settings for whoever deploys this. The fix is in each row."}
              </p>
            </div>
          </section>

          <Panel>
            <ul className="divide-y divide-line">
              {data.map((check) => (
                <li key={check.id} className="flex gap-3 py-4 first:pt-0 last:pb-0">
                  <span className="mt-0.5 shrink-0">{statusIcon[check.status]}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="font-medium">{check.title}</p>
                      <span className="text-xs text-muted">{statusWord[check.status]}</span>
                    </div>
                    <p className="mt-0.5 text-sm text-muted">{check.detail}</p>
                    {check.attacks && <RedTeam attacks={check.attacks} />}
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
        </>
      )}
    </div>
  );
}
