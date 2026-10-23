import { AnimatePresence, motion } from "motion/react";
import { ArrowUp, Brain, ShieldCheck, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { ask, ApiError } from "../lib/api";
import { useAsk, useSession } from "../lib/context";

type Message = { role: "user" | "assistant"; content: string; refused?: boolean; engine?: "claude" | "rules" };

const SUGGESTIONS = [
  "Where did my money go this month?",
  "How much am I paying for subscriptions?",
  "Did anything weird hit my card recently?",
  "Am I spending more than last month?",
  "How can I save more?",
];

/** Streams an answer with $ amounts set in tabular numerals so they line up while text arrives. */
function AnswerText({ text }: { text: string }) {
  const parts = text.split(/(\$[0-9][0-9,]*(?:\.[0-9]{2})?)/g);
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith("$") ? (
          <strong key={i} className="num font-semibold">
            {part}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

export function AskPanel() {
  const { open, prefill, closeAsk } = useAsk();
  const { session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const opener = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      opener.current = document.activeElement as HTMLElement | null;
      if (prefill) setInput(prefill);
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      opener.current?.focus?.(); // hand focus back to whatever opened the panel
    }
  }, [open, prefill]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && open && closeAsk();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closeAsk]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || busy) return;
    setNotice(null);
    setInput("");
    setBusy(true);
    // Blocked questions and their refusals never go back to the model (the server re-checks too).
    const history = messages.filter((m) => !m.refused && m.content).map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: q }, { role: "assistant", content: "" }]);
    const patchLast = (fn: (m: Message) => Message) =>
      setMessages((all) => [...all.slice(0, -1), fn(all[all.length - 1])]);
    try {
      await ask(q, history, (event) => {
        if (event.type === "meta") {
          setMessages((all) => {
            const out = [...all];
            out[out.length - 1] = { ...out[out.length - 1], refused: event.refused, engine: event.engine };
            if (event.refused) out[out.length - 2] = { ...out[out.length - 2], refused: true };
            return out;
          });
        }
        if (event.type === "delta") patchLast((m) => ({ ...m, content: m.content + event.text }));
      });
      patchLast((m) => (m.content ? m : { ...m, content: "I couldn't come up with an answer to that. Try asking another way." }));
    } catch (e) {
      setMessages((all) => all.slice(0, -2));
      setInput(q);
      setNotice(e instanceof ApiError && e.status === 429 ? "You're asking fast. Give it a few seconds." : (e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    send(input);
  };

  const engine = session?.ai_engine === "claude" ? "Claude" : "Rules engine";

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-[rgb(10_18_38/0.35)] backdrop-blur-[2px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeAsk}
          />
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label="Ask Money Brain"
            className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[480px] flex-col border-l border-line bg-raised shadow-2xl"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 380, damping: 38 }}
          >
            <header className="flex items-center justify-between border-b border-line px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-mint-soft text-good">
                  <Brain size={20} />
                </span>
                <div>
                  <h2 className="display text-lg font-semibold leading-tight">Money Brain</h2>
                  <p className="text-xs text-muted">Answers from your numbers. Powered by {engine}.</p>
                </div>
              </div>
              <button onClick={closeAsk} className="rounded-lg p-2 text-muted hover:bg-sunken hover:text-ink" aria-label="Close">
                <X size={18} />
              </button>
            </header>

            <div ref={listRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
              {messages.length === 0 && (
                <div>
                  <p className="display mb-4 text-2xl font-medium leading-snug">What do you want to know about your money?</p>
                  <div className="flex flex-col items-start gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button key={s} onClick={() => send(s)} className="rounded-full border border-line px-3.5 py-1.5 text-left text-sm hover:border-mint hover:bg-mint-soft">
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m, i) =>
                m.role === "user" ? (
                  <div key={i} className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-sm text-bg">
                    {m.content}
                  </div>
                ) : m.refused ? (
                  <div key={i} className="flex max-w-[92%] gap-3 rounded-2xl border border-line bg-sunken px-4 py-3 text-sm">
                    <ShieldCheck size={18} className="mt-0.5 shrink-0 text-good" />
                    <div>
                      <p className="mb-0.5 font-medium">Blocked by a safety rule</p>
                      <p className="text-muted">{m.content}</p>
                    </div>
                  </div>
                ) : (
                  <div key={i} className="max-w-[92%] text-[15px] leading-relaxed">
                    {m.content ? <AnswerText text={m.content} /> : <span className="inline-block h-4 w-16 animate-pulse rounded bg-sunken align-middle" />}
                    {m.engine && m.content && <div className="mt-1.5 text-xs text-muted">{m.engine === "claude" ? "Claude" : "Rules engine"}</div>}
                  </div>
                ),
              )}
            </div>

            <form onSubmit={onSubmit} className="border-t border-line p-4">
              {notice && <p className="mb-2 text-sm text-coral-text">{notice}</p>}
              <div className="flex items-end gap-2 rounded-2xl border border-line bg-bg p-2 focus-within:border-mint">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value.slice(0, 500))}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send(input);
                    }
                  }}
                  rows={1}
                  placeholder="Ask about your spending"
                  className="max-h-32 min-h-[40px] flex-1 resize-none bg-transparent px-2 py-2 text-[15px] outline-none focus-visible:outline-none placeholder:text-muted"
                  aria-label="Your question"
                />
                <button type="submit" disabled={busy || !input.trim()} aria-label="Send" className="grid h-10 w-10 place-items-center rounded-xl bg-mint text-mint-ink transition disabled:opacity-40">
                  <ArrowUp size={18} />
                </button>
              </div>
              <p className="mt-2 text-xs text-muted">It reads your numbers. It can't move money or give investment advice.</p>
            </form>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
