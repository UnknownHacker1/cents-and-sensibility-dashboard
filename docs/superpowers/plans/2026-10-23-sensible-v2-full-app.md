# Sensible v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Sensible into a React + FastAPI product covering Events 1 to 5.

**Architecture:** FastAPI (`api/`) wraps the tested `money/` core and serves the built React app (`web/`). Claude and Plaid are optional and degrade to the rules engine and fake bank.

**Tech Stack:** Python 3.11, FastAPI, Starlette sessions, anthropic SDK, plaid-python, pytest. React 19, Vite, TypeScript, Tailwind v4, react-router, Recharts, motion, lucide-react, react-plaid-link.

**Spec:** `docs/superpowers/specs/2026-10-23-sensible-v2-full-app-design.md`

## Global Constraints

- Model `claude-opus-5-5`, effort `low`, `fallbacks="default"` with beta `server-side-fallback-2026-07-01`.
- Keys only from env: `ANTHROPIC_API_KEY`, `PLAID_CLIENT_ID`, `PLAID_SECRET`, `SECRET_KEY`, `APP_PASSWORD`.
- Ask: question <= 500 chars, history <= 8 turns, 10 requests / 60 s / session.
- Colors and fonts exactly as the spec's token list.
- Tests never hit the network.

## Review Focus

- Prompt-injection text inside a merchant name: guardrails still apply, and the model is told merchant text is data.
- Claude API error mid-request: the user still gets the rules answer, never a stack trace.
- Plaid exchange with a bad public token: 400 with Plaid's error code, session stays on the fake bank.
- Expired or forged session cookie: 401, not 500.
- Month query param that is malformed or absent from the data: 422 or a fallback to the latest month, no crash.

---

### Task 1: money core additions
**Files:**
- `money/analytics.py`: `pace(tx, month) -> list[dict]` with `{day, this_month, last_month}`, cumulative, `this_month` None after today
- `money/story.py`: `month_story(tx, month, today) -> list[dict]`
- `money/ai.py`: `stream_answer(question, accounts, tx, history=(), today=None, client=None) -> Iterator[dict]`
- `money/plaid_bank.py`: `create_link_token(user_id)`, `exchange_public_token(token)`, `PlaidSandboxBank.from_access_token`

**Tests:**
- pace length equals days in month, cumulative and non-decreasing
- story mentions the spent amount and top alert, handles an empty month
- ai refuses before calling the client
- ai uses rules with no key
- ai streams deltas from a fake client
- ai falls back to rules when the client raises

### Task 2: FastAPI app
**Files:**
- `api/__init__.py`, `api/main.py` (app factory `create_app(settings)`)
- `api/settings.py`, `api/security.py` (headers, rate limiter, security checks), `api/state.py` (session store)
- `tests/test_api.py`

**Tests:**
- 401 without login
- demo login works, wrong password 401
- dashboard keys present
- bad month 422
- ask SSE has meta/delta/done
- 11th ask in a minute 429
- headers present on every response
- Plaid link token 503 when keys missing
- exchange stores the token server-side and it never appears in any response
- security checks list of 9 with guardrail red team passing

### Task 3: Web scaffold + design system
- Vite React TS in `web/`, Tailwind v4, fonts, tokens in CSS variables (light/dark), API client with SSE parser, router, app shell.
- Verify: `npm run build` and `tsc` clean.

### Task 4: Overview page
- Story, accounts strip, pace chart, category bars, alerts, subscriptions, goal.
- Verify in the browser (desktop, 375px, dark).

### Task 5: Ask panel, Transactions, Connect, Security pages
- Verify each in the browser: streaming answer, refusal styling, filters, Plaid button disabled state with a clear reason, security checks render.

### Task 6: Landing + login
- Verify the hero renders with live data and the CTA reaches the demo.

### Task 7: Ship
- `.env.example`, devcontainer (Node + Python, build, serve on 8000), README, `docs/demo-script.md`, `requirements.txt`.
- Full pytest, `npm run build`, browser check through FastAPI on :8000, code review subagent, commit, push.
