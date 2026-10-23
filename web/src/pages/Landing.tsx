import { motion } from "motion/react";
import type { ReactNode } from "react";
import { AlertTriangle, Brain, KeyRound, Lock, Moon, ShieldCheck, Sun, UserX } from "lucide-react";
import { Link } from "react-router-dom";
import { PaceChart } from "../components/charts";
import { Story } from "../components/Story";
import { Skeleton, Wordmark } from "../components/ui";
import { api } from "../lib/api";
import { useSession } from "../lib/context";
import { money, monthName, shortDate } from "../lib/format";
import { useLoad, usePrefersReducedMotion, useTheme } from "../lib/hooks";

const today = new Date();
const thisMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;

function Reveal({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  const reduced = usePrefersReducedMotion();
  if (reduced) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}

const PROMISES = [
  { icon: UserX, title: "Fake data until you say otherwise", body: "Starts on a made-up bank. Plaid's Sandbox is the only bank it can reach. No real logins, ever." },
  { icon: KeyRound, title: "Keys never touch the browser", body: "Plaid and Claude keys live in the server's .env. Bank tokens stay in server memory and vanish when you sign out." },
  { icon: Lock, title: "Locked by default", body: "Signed httpOnly session cookie, strict security headers, and a rate limit on the assistant." },
  { icon: ShieldCheck, title: "Guardrails it can't talk itself out of", body: "It won't move money, give investment advice, or follow a prompt that tells it to ignore its rules." },
];

export function Landing() {
  const { data } = useLoad(() => api.preview(), []);
  const { session } = useSession();
  const { theme, toggle } = useTheme();
  const cta = session?.authenticated ? "/app" : "/login";
  const ctaLabel = session?.authenticated ? "Open your dashboard" : "Open the demo";

  return (
    <div className="min-h-screen overflow-x-hidden">
      <nav className="mx-auto flex max-w-[1180px] items-center justify-between px-4 py-5 sm:px-6">
        <Wordmark />
        <div className="flex items-center gap-2">
          <button onClick={toggle} aria-label="Toggle dark mode" className="rounded-lg p-2 text-muted hover:bg-sunken hover:text-ink">
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link to={cta} className="rounded-[10px] bg-ink px-4 py-2 text-sm font-medium text-bg hover:opacity-90">
            {ctaLabel}
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <header className="mx-auto grid max-w-[1180px] items-center gap-12 px-4 pb-20 pt-10 sm:px-6 lg:grid-cols-[1.15fr_1fr] lg:pt-16">
        <Reveal>
          <h1 className="display text-[clamp(2.6rem,5.6vw,4.6rem)] font-bold leading-[0.98] tracking-[-0.035em]">
            Your money,
            <br />
            finally making{" "}
            <span className="relative whitespace-nowrap">
              <span className="relative z-10">sense.</span>
              <svg viewBox="0 0 200 20" preserveAspectRatio="none" className="absolute -bottom-1 left-0 z-0 h-[0.32em] w-full" aria-hidden="true">
                <path d="M3 14 C 50 4, 120 4, 197 10" fill="none" stroke="var(--mint)" strokeWidth="9" strokeLinecap="round" />
              </svg>
            </span>
          </h1>
          <p className="mt-6 max-w-[34rem] text-lg leading-relaxed text-muted">
            Sensible puts every account in one place, explains your month in a single sentence, and taps you on the shoulder when a charge looks off.
            Then you can just ask it.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to={cta} className="rounded-xl bg-mint px-6 py-3 text-base font-semibold text-mint-ink shadow-panel transition hover:brightness-95">
              {ctaLabel}
            </Link>
            <a href="#ask" className="rounded-xl px-4 py-3 text-base font-medium text-ink hover:bg-sunken">
              See what it says
            </a>
          </div>
          <p className="mt-5 text-sm text-muted">Runs on fake data. Nothing to sign up for.</p>
        </Reveal>

        {/* Live product preview, built from the same API the app uses */}
        <Reveal delay={0.12}>
          <div className="relative">
            <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-[radial-gradient(60%_60%_at_70%_30%,var(--mint-soft),transparent_70%)]" aria-hidden="true" />
            <div className="rounded-3xl border border-line bg-raised p-6 shadow-[0_30px_80px_-30px_rgb(20_33_61/0.35)] sm:p-7 sm:pb-20">
              <div className="mb-5 flex items-center justify-between text-sm text-muted">
                <span>{monthName(thisMonth)} so far</span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-mint" aria-hidden="true" /> Live demo data
                </span>
              </div>
              {data ? (
                <>
                  <Story tokens={data.story} size="lg" />
                  <div className="mt-6">
                    <PaceChart data={data.pace} thisLabel={monthName(thisMonth)} lastLabel={monthName(thisMonth, -1)} height={180} />
                  </div>
                </>
              ) : (
                <div className="space-y-3">
                  <Skeleton className="h-8 w-11/12" />
                  <Skeleton className="h-8 w-3/4" />
                  <Skeleton className="mt-6 h-44" />
                </div>
              )}
            </div>
            {data?.alerts[0] && (
              <motion.div
                initial={{ opacity: 0, y: 12, rotate: 0 }}
                animate={{ opacity: 1, y: 0, rotate: -2 }}
                transition={{ delay: 0.9, type: "spring", stiffness: 200, damping: 18 }}
                className="absolute -bottom-10 -left-4 hidden max-w-[260px] rounded-2xl border border-line bg-raised p-4 shadow-[0_20px_50px_-20px_rgb(20_33_61/0.45)] sm:block lg:-left-10"
              >
                <p className="flex items-center gap-2 text-sm font-semibold text-coral-text">
                  <AlertTriangle size={15} /> This looks off
                </p>
                <p className="mt-1 text-sm">
                  <span className="num font-semibold">{money(data.alerts[0].amount)}</span> at {data.alerts[0].merchant}
                </p>
                <p className="mt-0.5 text-xs text-muted">{data.alerts[0].reason.split(";")[0]}</p>
              </motion.div>
            )}
          </div>
        </Reveal>
      </header>

      {/* Ask */}
      <section id="ask" className="border-y border-line bg-raised py-20">
        <div className="mx-auto grid max-w-[1180px] gap-12 px-4 sm:px-6 lg:grid-cols-[0.8fr_1.2fr]">
          <Reveal>
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-ink text-bg">
              <Brain size={22} />
            </span>
            <h2 className="display mt-5 text-4xl font-semibold leading-tight">Ask it like you'd ask a friend who's good with money.</h2>
            <p className="mt-4 text-muted">
              Money Brain answers from your actual numbers, not vibes. Every dollar amount it says comes straight from your transactions. Add a Claude key
              and it gets conversational; without one, a rules engine still answers the common questions.
            </p>
          </Reveal>
          <div className="space-y-4">
            {(data?.examples ?? []).map((ex, i) => (
              <Reveal key={ex.question} delay={i * 0.08}>
                <div className="rounded-2xl border border-line bg-bg p-5">
                  <p className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-ink px-4 py-2 text-sm text-bg">{ex.question}</p>
                  <p className="mt-3 max-w-[92%] text-[15px] leading-relaxed">{ex.answer}</p>
                </div>
              </Reveal>
            ))}
            {!data && <Skeleton className="h-64" />}
          </div>
        </div>
      </section>

      {/* Notices */}
      <section className="mx-auto max-w-[1180px] px-4 py-20 sm:px-6">
        <Reveal>
          <h2 className="display max-w-2xl text-4xl font-semibold leading-tight">It notices the charge you'd have missed.</h2>
          <p className="mt-4 max-w-2xl text-muted">
            Two rules, no magic. A charge three times bigger than what you usually spend at that kind of place, or a first-time merchant over $200.
          </p>
        </Reveal>
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {(data?.alerts ?? []).map((a, i) => (
            <Reveal key={a.merchant} delay={i * 0.08}>
              <div className="flex h-full gap-4 rounded-2xl border border-line border-l-[3px] border-l-coral bg-raised p-5 shadow-panel">
                <div className="flex-1">
                  <div className="flex items-baseline justify-between gap-3">
                    <p className="font-semibold">{a.merchant}</p>
                    <p className="display num text-2xl font-semibold">{money(a.amount)}</p>
                  </div>
                  <p className="text-sm text-muted">
                    {shortDate(a.date)}, {a.category}
                  </p>
                  <p className="mt-3 text-sm">{a.reason[0].toUpperCase() + a.reason.slice(1)}.</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Security */}
      <section className="bg-ink py-20 text-bg">
        <div className="mx-auto max-w-[1180px] px-4 sm:px-6">
          <Reveal>
            <h2 className="display max-w-2xl text-4xl font-semibold leading-tight">Built like the bank is watching.</h2>
            <p className="mt-4 max-w-2xl opacity-75">The app grades itself. Open the Security Center and it runs nine checks live, including a red-team pass against its own assistant.</p>
          </Reveal>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {PROMISES.map(({ icon: Icon, title, body }, i) => (
              <Reveal key={title} delay={i * 0.06}>
                <Icon size={22} className="text-mint" />
                <p className="mt-3 font-semibold">{title}</p>
                <p className="mt-1.5 text-sm leading-relaxed opacity-75">{body}</p>
              </Reveal>
            ))}
          </div>
          <Link to={cta} className="mt-12 inline-block rounded-xl bg-mint px-6 py-3 font-semibold text-mint-ink hover:brightness-95">
            {ctaLabel}
          </Link>
        </div>
      </section>

      <footer className="mx-auto flex max-w-[1180px] flex-col gap-3 px-4 py-10 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <Wordmark className="text-base" />
        <p>Built by Cents &amp; Sensibility for the FinTech Club Innovation Series. Not financial advice.</p>
      </footer>
    </div>
  );
}
