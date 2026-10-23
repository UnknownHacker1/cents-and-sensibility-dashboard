import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary: "bg-mint text-mint-ink hover:brightness-95 active:brightness-90",
  secondary: "bg-raised text-ink border border-line hover:bg-sunken",
  ghost: "text-ink hover:bg-sunken",
  danger: "bg-raised text-coral-text border border-line hover:bg-coral-soft",
};

export function Button({
  variant = "secondary",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[10px] px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

/** A section of the page. Sits on a raised surface; the title is a plain sentence-case heading. */
export function Panel({
  title,
  aside,
  children,
  className = "",
  id,
}: {
  title?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={`rounded-2xl border border-line bg-raised p-5 shadow-panel sm:p-6 ${className}`}>
      {(title || aside) && (
        <header className="mb-4 flex items-baseline justify-between gap-3">
          {title && <h2 className="display text-lg font-semibold">{title}</h2>}
          {aside && <div className="text-sm text-muted">{aside}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-sunken ${className}`} />;
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex items-center justify-between gap-4 rounded-xl border border-line bg-coral-soft px-4 py-3 text-sm">
      <span>{message}</span>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`display inline-flex items-center gap-2 text-xl font-bold ${className}`}>
      <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="var(--ink)" />
        <path
          d="M9 21.5c1.6 1.3 3.9 2 6.4 2 3.6 0 5.9-1.7 5.9-4.3 0-2.4-1.6-3.5-5.2-4.2-2.6-.5-3.5-1-3.5-2.1 0-1.1 1.1-1.8 2.9-1.8 1.7 0 3 .5 4.2 1.4"
          fill="none"
          stroke="var(--mint)"
          strokeWidth="2.6"
          strokeLinecap="round"
        />
      </svg>
      Sensible
    </span>
  );
}
